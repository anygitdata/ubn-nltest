(function($) {	$(document).ready(function () {

    "use strict";

    const sContentDetail = '#content-detail';   // div детализации
    const mainWrapper = $('.main-content');   // div основного интерфейса
    let id_loadContent = '';    // Строковый идентифЗагруженной детализации

    // ********************************************************************

    // Глобальная процедура ОБНОВЛЕНИЯ интерфейса пользователя
    // после загрузки детализации по ajax
    function toggleHtml (order='mainDur', mainDur=800, detailDur=1200){
        if (order === 'mainDur') {
            mainWrapper.fadeOut(mainDur);
            $(sContentDetail).fadeIn(detailDur)
        }
        else {
            $(sContentDetail).fadeOut(detailDur)
            mainWrapper.fadeIn(mainDur);
        }

        }

    // начальная настройка интерфейса (включая меню)
    (function (detail) {

        $('.menu > ul > li:has( > ul)').addClass('menu-dropdown-icon');
        $('.menu > ul > li > ul:not(:has(ul))').addClass('normal-sub');
        $(".menu > ul").before("<span class=\"menu-mobile\">Меню:</span>");
        $(".menu > ul > li").hover(function (e) {
            if ($(window).width() > 768) {
                $(this).children("ul").stop(true, false).fadeToggle(150);
                e.preventDefault();
            }
        });
        $(".menu > ul > li").click(function () {
            if ($(window).width() <= 768) {
                $(this).children("ul").fadeToggle(150);
            }
        });
        $(".menu-mobile").click(function (e) {
            $(".menu > ul").toggleClass('show-on-mobile');
            e.preventDefault();
        });

        // Начальная настройка div детализации
        const divDetail = $(detail);
        divDetail.hide();
        let btn = $("<button id='btn_content-detail'>Назад</button>");
        divDetail.append(btn).append($('<div />'))

        // Обработчик скрытие детализации
        $('#btn_content-detail').click(function(e){
            toggleHtml('closeDet', 800, 1200);
        })

    }(sContentDetail));

        });
    })(jQuery);
