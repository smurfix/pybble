/**
 * js.overall
 * ~~~~~~~~~~
 *
 * Some general scripts for the whole portal (requires jQuery).
 *
 * :copyright: 2007-2008 by Christoph Hack, Armin Ronacher, Benjamin Wiegand.
 * :license: GNU GPL.
 */

$(document).ready(function() {
  // konqueror fix
  with ($.browser) {
    safari = safari || !!navigator.appName.match(/konqueror/i)
  };

//  var loginForm = null;
//
//  // preload images
//  (function() {
//    var container = $('<div>')
//      .appendTo('body')
//      .css({height: 0, overflow: 'hidden'});
//    $.each(['img/tabbar_border_hover.png'], function() {
//      $('<img />')
//        .attr('src', $STATIC_URL + this)
//        .appendTo(container);
//    });
//  })();

  // add a hide message link to all flash messages
  $.each($('div.message'), function(i, elm) {
    $(elm).prepend($('<a href="#" class="hide" />')
      .click(function() {
//        if ($(this).parent().hasClass('global')) {
//          $.post('/?__service__=portal.hide_global_message', {});
//        }
        $(this).parent().slideUp('slow');
        return false;
      })
    )
  });

//  // hide search words on click
//  $('a.hide_searchwords')
//    .click(function() {
//      $(this).parent().slideUp('slow');
//      $('span.highlight').removeClass('highlight');
//      return false;
//    });
//
//  // add a link to the user map if javascript available and on the index page
//  (function() {
//    var navigation = $('h3.navi_ubuntuusers').next();
//    if (navigation.is('ul'))
//      $('<li><a href="/map/">Benutzerkarte</a></li>')
//        .appendTo(navigation);
//  })();
//
//  // create a link to hide a toc
//  $('.toc .head').append(
//    $('<a> [-]</a>').toggle(function() {
//        $(this).text(' [+]').parent().parent().find('ol').hide();
//      },
//      function() {
//        $(this).text(' [-]').parent().parent().find('ol').show();
//      }
//    )
//  );
//
//  // if we have JavaScript we style the search bar so that it looks
//  // like a firefox search thingy and apply some behavior
//  (function() {
//    if (navigator.appName.toLowerCase() == 'konqueror')
//      return
//    var
//      initialized = false,
//      $currentSearchArea = $('select.search_area').val(),
//      $currentAreaName = $('select.search_area option[@selected]').html(),
//      areaPopup = $('<ul class="search_area" />'),
//      searchArea = $('select.search_area').hide();
//      $('.search_query').addClass('area_' + $currentSearchArea);
//    $('form.search')
//      .submit(function() {
//        var url = $(this).attr('action'),
//            tmp = $('input.search_query').val();
//        if ($('input.search_query').hasClass('default_value'))
//          tmp = '';
//        if (tmp) {
//          url += '?query=' + encodeURIComponent(tmp);
//          if ($currentSearchArea != 'all')
//            url += '&area=' + $currentSearchArea;
//        }
//        document.location.href = url;
//        return false;
//      })
//      .append($('<div class="search_expander" />')
//        .click(function() {
//          if (!initialized) {
//            initialized = true;
//            $('option', searchArea).each(function() {
//              var currentArea = $(this).val();
//              var item = $('<li />')
//                .text($(this).text())
//                .addClass('area_' + $(this).val())
//                .click(function() {
//                  $currentAreaName = $(this).html();
//                  $('.search_query').removeClass('area_' + $currentSearchArea);
//                  $currentSearchArea = currentArea;
//                  $currentAreaName = $('select.search_area option[@value=' +
//                                       $currentSearchArea + ']').html()
//                  $('.search_query').addClass('area_' + $currentSearchArea);
//                  $('li', areaPopup).each(function() {
//                    $(this).removeClass('active');
//                  });
//                  $(this).addClass('active').parent();
//                  $('.search_query').focus();
//                  areaPopup.hide();
//                  return false;
//                }).appendTo(areaPopup);
//              if (currentArea == $currentSearchArea)
//                item.addClass('active');
//            });
//            areaPopup.prependTo('form.search');
//          }
//          else areaPopup.toggle();
//          return false;
//        }));
//      $('.search_query').addClass('search_query_js')
//        .blur(function() {
//          var e = $(this);
//          if (e.val() == '')
//            e.addClass('default_value').val($currentAreaName);
//        })
//        .focus(function() {
//          var e = $(this);
//          if (e.hasClass('default_value'))
//            e.val('').removeClass('default_value');
//        });
//      $('.search_query').blur();
//    $(document).click(function() {
//      if (areaPopup.is(':visible'))
//        areaPopup.hide();
//      if (loginForm && loginForm.is(':visible'))
//        loginForm.slideUp();
//    });
//  })();
//
//  // add a sidebar toggler if there is an sidebar
//  (function() {
//    var sidebar = $('.navi_sidebar');
//    if (!sidebar.length)
//      return;
//    var togglebutton =
//      $('<button class="navi_toggle_up" title="Navigation ausblenden" />')
//        .click(function() {
//          $('.content').toggleClass('content_sidebar');
//          sidebar.toggle();
//          togglebutton
//            .toggleClass('navi_toggle_up')
//            .toggleClass('navi_toggle_down');
//          if ($IS_LOGGED_IN)
//            $.get('/?__service__=portal.toggle_sidebar', {
//              hide: !sidebar.is(':visible')
//            });
//          return false;
//        })
//        .insertAfter('form.search');
//    if ($SIDEBAR_HIDDEN)
//      togglebutton.click();
//  })();

  // use javascript to deactivate the submit button on click
  // we don't make the elements really disabled because then
  // the button won't appear in the form data transmitted
  (function() {
    var submitted = false;
    $('form').submit(function() {
      if (submitted)
        return false;
      $('input[@type="submit"]').addClass('disabled');
      submitted = true;
    });
  })();

//  // add links to the "package" macro
//  $('.package-list').each(function(i, elm) {
//    var tmp = $('.bash', elm), apt = tmp[0], aptitude = tmp[1];
//    $(aptitude).hide();
//    $($('p', elm)[0]).append(
//      $('<a>apt-get</a>').click(function() {
//        $(this).parent().children().css('font-weight', '');
//        $(this).css('font-weight', 'bold');
//        $(apt).show();
//        $(aptitude).hide();
//      }).click(), ' ',
//      $('<a>aptitude</a>').click(function() {
//        $(this).parent().children().css('font-weight', '');
//        $(this).css('font-weight', 'bold');
//        $(aptitude).show();
//        $(apt).hide();
//      }), ' ',
//      $('<a>apturl</a>').attr('href', 'apt://' + $(apt).text().split(' ')
//                                                       .slice(3).join(','))
//    )
//  });
//
//  // the javascript powered login form
//  (function() {
//    $('#login_link').click(function() {
//      if (loginForm == null) {
//        loginForm = $('#js_login_form')
//          .prependTo('body')
//          .submit(function(event) {
//            loginForm.slideDown();
//            return true;
//          })
//          .click(function(event) {
//            event.stopPropagation();
//          });
//      }
//      loginForm.fadeIn();
//      $('#js_login_username').focus();
//      return false;
//    });
//  })();
});
