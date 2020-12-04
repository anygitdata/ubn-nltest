(function ($) {
    $(document).ready(function () {

        "use strict";

        const sContentDetail = '#content-detail';   // div детализации
        const mainWrapper = $('.main-content');   // div основного интерфейса
        let id_loadContent = '';    // Строковый идентифЗагруженной детализации

        // ********************************************************************

        // Глобальная процедура ОБНОВЛЕНИЯ интерфейса пользователя
        // после загрузки детализации по ajax
        function toggleHtml(order = 'mainDur', mainDur = 800, detailDur = 1200) {
            if (order === 'mainDur') {
                mainWrapper.fadeOut(mainDur);
                $(sContentDetail).fadeIn(detailDur)
            }
            else {
                $(sContentDetail).fadeOut(detailDur)
                mainWrapper.fadeIn(mainDur);
            }

            $("html,body").scrollTop($(sContentDetail)).offset().top;
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
            $('#btn_content-detail').click(function (e) {
                toggleHtml('closeDet', 800, 1200);
            })

        }(sContentDetail));

        // Обработчики загрузки по ajax
        (function (detail, main, loadContent) {

            // Обработчик загрузки детализации в <div id="content-detail" ...
            const fun_click = function (e) {
                const curID = $(e.currentTarget).prop('id');

                let div;
                if (loadContent !== curID) {
                    $.ajax({
                        url: "/preds/contentedstag", //  "{% url 'contentedstag' %}",
                        data: { file_tag: curID },
                        type: 'get',
                        dataType: 'html',

                        success: function (data) {

                            div = $(sContentDetail + ' div');
                            div.empty();
                            div.append(data);

                            loadContent = curID;
                            toggleHtml();
                        }
                    });
                }

                toggleHtml()

            }

            // Обработчик загрузки основного контента
            function load_content(id) {

                $.ajax({
                    url: "{% url 'contentedstag' %}",
                    data: { file_tag: id },
                    type: 'get',
                    dataType: 'html',
                    success: function (data) {

                        let div = $('#' + id);

                        div.empty();
                        div.html(data);
                    }

                });
            }

            // бработчик для динимически загружаемых элементов
            $(main).on('click', 'button', fun_click)

        }(sContentDetail, mainWrapper, id_loadContent)) // end Обработчики элементов, загружающие контент по ajax

    });
})(jQuery);
