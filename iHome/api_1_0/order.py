# -*- coding:utf-8 -*-
from . import api
from flask import request, jsonify, current_app, g
from iHome.utils.common import login_required
from iHome.utils.response_code import RET
from iHome.models import House, Order
import datetime
from iHome import db

@api.route('/orders/<int:order_id>/comment',methods=['POST'])
@login_required
def set_comment(order_id):
    comment = request.json.get('comment')
    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg='缺少必要的参数')
    # 使用user_id 查询订单
    try:
        order = Order.query.filter(Order.id == order_id, Order.user_id == g.user_id,
                                   Order.status == 'WAIT_COMMENT').first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询订单的数据失败')
    if not order:
        return jsonify(errno=RET.NODATA, errmsg='订单数据不存在')
    # 修改订单的状态为“已完成”
    order.comment = comment
    order.status = 'COMPLETE'

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='评论信息存储失败')
    # 响应结果
    return jsonify(errno=RET.OK, errmsg='OK')


@api.route('/orders/<int:order_id>', methods=['PUT'])
@login_required
def set_order_status(order_id):
    """接单"""
    # 1:查询order_id相关的信息
    # 获取action
    action = request.args.get('action')
    if action not in ['accept', 'reject']:
        return jsonify(errno=RET.PARAMERR, errmsg='缺少参数')
    try:
        order = Order.query.filter(Order.id == order_id, Order.status == 'WAIT_ACCEPT').first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='参数获取有误')
    if not order:
        return jsonify(errno=RET.NODATA, errmsg='订单不存在')
    # 判断登录的用户是否为房东
    login_user_id = g.user_id
    landlord_id = order.house.user_id
    if login_user_id != landlord_id:
        return jsonify(errno=RET.PARAMERR, errmsg='参数有误')
    # 修改订单的状态，将其改为待评价的状态，并存储到数据库中
    if action == 'accept':
        order.status = 'WAIT_COMMENT'
    else:
        order.status = 'REJECTED'
        reason = request.json.get('reason')
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg='缺少拒单的理由')
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='存储失败')
    # 响应结果
    return jsonify(errno=RET.OK, errmsg='Ok')


@api.route('/orders', methods=['GET'])
@login_required
def order_info():
    """我的订单和客户的订单的接口类似"""
    # 1：获取参数 user_id
    user_id = g.user_id
    role = request.args.get('role')
    if role not in ['custom', 'landlord']:
        return jsonify(errno=RET.PARAMERR, errmsg='参数有误')

    # 2；查询不同角色的订单的信息
    try:
        if role == 'custom':
            orders = Order.query.filter(Order.user_id == user_id).all()
        else:
            # 先查询该用户所发布的的房屋的信息
            houses = House.query.filter(House.user_id == user_id).all()
            houses_ids = [house.id for house in houses]
            # 再查询我发布的房屋在不在订单中
            orders = Order.query.filter(Order.house_id.in_(houses_ids)).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询客户获取有误')
    if not orders:
        return jsonify(errno=RET.NODATA, errmsg='订单数据不存在')
    # 3：构造响应的信息
    order_dict_list = []
    for order in orders:
        order_dict_list.append(order.to_dict())
    # 4：返回响应的结果
    return jsonify(errno=RET.OK, errmsg='OK', data=order_dict_list)


@api.route('/orders', methods=['POST'])
@login_required
def create_order():
    """创建订单"""
    json_dict = request.json
    house_id = json_dict.get('house_id')
    start_date_str = json_dict.get('start_date')
    end_date_str = json_dict.get('end_date')
    # 参数的校验
    if not all([house_id, start_date_str, end_date_str]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    # 创建House对象
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取参数有误')
    # 判断房屋是否存在
    if not house:
        return jsonify(errno=RET.NODATA, errmsg='房屋不存在')

    # 判断入住时间和离开时间是否合理
    try:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
        if start_date and end_date:
            assert start_date < end_date, Exception('参数有误')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数设置不合理')

    # 判断当前的房屋是否被预定：首先就要从数据库查找出有冲突的订单
    try:
        conflict_order = Order.query.filter(Order.house_id == house_id, end_date > Order.begin_date,
                                            start_date < Order.end_date).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='冲突订单的查询有误')

    # 2：判断是否存在当前的房屋被预定的情况

    if conflict_order:
        return jsonify(errno=RET.NODATA, errmsg='当前的房屋已被预定')
    # 创建模型的对象,储存订单的数据
    days = (end_date - start_date).days
    order = Order()
    order.user_id = g.user_id
    order.house_id = house_id
    order.begin_date = start_date
    order.end_date = end_date
    order.days = days
    order.house_price = house.price
    order.amount = order.days * order.house_price
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存订单的数据失败')

    return jsonify(errno=RET.OK, errmsg='OK')
