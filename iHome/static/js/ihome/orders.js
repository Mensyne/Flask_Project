//模态框居中的控制
function centerModals() {
    $('.modal').each(function (i) {   //遍历每一个模态框
        var $clone = $(this).clone().css('display', 'block').appendTo('body');
        var top = Math.round(($clone.height() - $clone.find('.modal-content').height()) / 2);
        top = top > 0 ? top : 0;
        $clone.remove();
        $(this).find('.modal-content').css("margin-top", top - 30);  //修正原先已经有的30个像素
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function () {
    $('.modal').on('show.bs.modal', centerModals);      //当模态框出现的时候
    $(window).on('resize', centerModals);

    // TODO: 查询我的订单
    $.get('/api/1.0/orders?role=custom', function (response) {
        if (response.errno == '0') {
            var html = template('orders-list-tmpl', {'orders': response.data});
            $('.orders-list').html(html);
            // TODO: 查询成功之后需要设置评论的相关处理
            $(".order-comment").on("click", function () {
                var orderId = $(this).parents("li").attr("order-id");
                $(".modal-comment").attr("order-id", orderId);
            });
            $('.modal-comment').on('click', function () {
                var orderId = $('.modal-comment').attr('order-id');
                var comment = $('#comment').val();
                if (!comment) {
                    alert('请输入评论信息');
                    return;
                }
                $.ajax({
                    url: '/api/1.0/orders/' + orderId + '/comment',
                    type: 'post',
                    data: JSON.stringify({'comment': comment}),
                    contentType: 'application/json',
                    headers: {'X-CSRFToken': getCookie("csrf_token")},
                    success: function (response) {
                        if (response.errno == '0') {
                            $(".orders-list>li[order-id=" + orderId + "]>div.order-content>div.order-text>ul li:eq(4)>span").html("已完成");
                            // 2. 隐藏接单和拒单操作
                            $("ul.orders-list>li[order-id=" + orderId + "]>div.order-title>div.order-operate").hide();
                            // 3. 隐藏弹出的框
                            $("#comment-modal").modal("hide");
                        } else if (response.errno == '4101') {
                            location.href = '/'
                        } else {
                            alert(response.errmsg)
                        }
                    }
                })
            })

        } else if (response.errno == '4101') {
            location.href='/';

        } else {
            alert(response.errmsg)
        }

    });

});
