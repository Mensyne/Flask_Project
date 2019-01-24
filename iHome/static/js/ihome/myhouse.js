$(document).ready(function () {
    // TODO: 对于发布房源，只有认证后的用户才可以，所以先判断用户的实名认证状态
    $.get('/api/1.0/users/auth', function (response) {
        if (response.errno == '0') {
            //当用户有实名认证的信息时，展示实名认证信息
            if (response.data.real_name && response.data.id_card) {
                // 当用户具有实名认证信息时，展示实现认证的信息
                $.get('/api/1.0/users/houses', function (response) {
                    if (response.errno == '0') {
                        var html = template('houses-list-tmpl', {'houses': response.data});
                        $('#houses-list').html(html)
                    } else if (response.errno == '4101') {
                        location.href = '/'
                    } else {
                        alert(response.errmsg)
                    }

                })
            } else {
                // TODO: 如果用户已实名认证,那么就去请求之前发布的房源
                $(".auth-warn").show();
            }
        } else if (response.error == '4101') {
            location.href = '/'
        } else {
            alert(response.errmsg)
        }
    });
});



