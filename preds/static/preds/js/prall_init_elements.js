(function ($) {
    $(document).ready(function () {

        "use strict";

        const sContentDetail = $('#content-detail'); // div детализации
        const mainContent = $('.main-content');   // испТолько для init обработчиков button
        const mainCol = $('.main-col');           // div центральной колонки
        let id_loadContent = '';    // Строковый идентифЗагруженной детализации

        // ********************************************************************

        // Глобальная процедура ОБНОВЛЕНИЯ интерфейса пользователя
        // после загрузки детализации по ajax
        function toggleHtml(order = 'mainDur', mainDur = 1200, detailDur = 800) {
            if (order === 'mainDur') {
                mainCol.fadeOut(mainDur);
                sContentDetail.fadeIn(detailDur)
                // console.log('Детализация')
            }
            else {
                sContentDetail.fadeOut(detailDur)
                mainCol.fadeIn(mainDur);
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
            // const divDetail = detail;
            detail.hide();
            let btn = $("<button id='btn_content-detail'>Назад</button>");
            detail.append(btn).append($('<div />'))

            // Обработчик скрытие детализации
            $('#btn_content-detail').click(function (e) {
                e.preventDefault();
                toggleHtml('closeDet', 800, 1200);
            })

        }(sContentDetail));

        // Обработчики загрузки по ajax
        (function (main, loadContent) {

            // Обработчик загрузки детализации в <div id="content-detail" ...
            const fun_click = function (e) {

                e.preventDefault();

                const curID = $(e.currentTarget).prop('id');

                let div;
                if (loadContent !== curID) {
                    $.ajax({
                        url: "/preds/contentedstag", //  "{% url 'contentedstag' %}",
                        data: { file_tag: curID },
                        type: 'get',
                        dataType: 'html',

                        success: function (data) {
                            div = $('#content-detail div');
                            div.empty();
                            div.append(data);

                            loadContent = curID;
                            toggleHtml();
                        }
                    });
                }
                else
                    toggleHtml()

            }


            // бработчик для динимически загружаемых элементов
            $(main).on('click', '.btn-detail-cont', fun_click)

        }(mainContent, id_loadContent)) // end Обработчики элементов, загружающие контент по ajax

    });
})(jQuery);
