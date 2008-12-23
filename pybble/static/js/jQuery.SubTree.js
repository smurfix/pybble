// jQuery File Tree Plugin
//
// Version 1.01
//
// Cory S.N. LaViska
// A Beautiful Site (http://abeautifulsite.net/)
// 24 March 2008
//
// Visit http://abeautifulsite.net/notebook.php?article=58 for more information
//
// Usage: $('.subTreeDemo').subTree( options, callback )
//
// Options:  script         - location of the serverside AJAX file to use
//           folderEvent    - event to trigger expand/collapse; default = click
//           expandSpeed    - default = 500 (ms); use -1 for no animation
//           collapseSpeed  - default = 500 (ms); use -1 for no animation
//           expandEasing   - easing function to use on expand (optional)
//           collapseEasing - easing function to use on collapse (optional)
//           multiFolder    - whether or not to limit the browser to one subfolder at a time
//
// History:
//
// 1.01 - updated to work with foreign characters in directory/file names (12 April 2008)
// 1.00 - released (24 March 2008)
//
// heavily modified by Matthias Urlichs <matthias@urlichs.de> for Pybble
//
// TERMS OF USE
// 
// jQuery File Tree is licensed under a Creative Commons License and is copyrighted (C)2008 by Cory S.N. LaViska.
// For details, visit http://creativecommons.org/licenses/by/3.0/us/
//
if(jQuery) (function($){
	
	$.extend($.fn, {
		subTree: function(o) {
			// Defaults
			if( !o ) var o = {};
			if( !o.script ) return;
			if( o.folderEvent == undefined ) o.folderEvent = 'click';
			if( o.expandSpeed == undefined ) o.expandSpeed= 500;
			if( o.collapseSpeed == undefined ) o.collapseSpeed= 500;
			if( o.expandEasing == undefined ) o.expandEasing = null;
			if( o.collapseEasing == undefined ) o.collapseEasing = null;
			
			$(this).each( function() {
				function showTree(c, t) {
					if( ! $(c).children('ul').length ) {
						$(c).addClass('wait');
						if (o.discr) t = t+"/"+o.discr
						$.post(o.script, { dir: t }, function(data) {
							var ul = document.createElement("ul")
							$(c).removeClass('wait');
							$(ul).css("display","hidden")
							$(ul).html(data)
							$(c).append(ul)
							$(c).children('UL:hidden').slideDown({ duration: o.expandSpeed, easing: o.expandEasing });
							// $(c).children('UL:hidden').show();
							bindTree(c);
						});
					}
					// $(c).children('ul:hidden').show();
					$(c).children('UL:hidden').slideDown({ duration: o.expandSpeed, easing: o.expandEasing });
				}
				function clickExpand(target) {
					if( $(target).hasClass('collapsed') ) {
						// Expand
						showTree( $(target), $(target).attr('rel'));
						$(target).removeClass('collapsed').addClass('expanded');
					} else if( $(target).hasClass('expanded') ) {
						// Collapse
						$(target).children('UL').slideUp({ duration: o.collapseSpeed, easing: o.collapseEasing });
						// $(target).children('UL').hide();
						$(target).removeClass('expanded').addClass('collapsed');
					} else {
						return true;
					}
					return false;
				}
				function clickLoad(target) {
					var c = target;
					var div = $(c).children('div.content')
					if( ! div.length ) {
						$(c).addClass('wait_content');
						$.post(o.cscript, { dir: $(target).attr('rel') }, function(data) {
							div = document.createElement("div");
							$(div).addClass("content");
							$(c).removeClass('wait_content');
							$(div).css("display","hidden");
							$(div).html(data);
							$(c).children('a.content').filter(":first").after(div);
							$(c).children('div.content:hidden').slideDown({ duration: o.expandSpeed, easing: o.expandEasing });
							// $(c).children('div.content:hidden').show();
						});
					} else if (div.filter(":hidden").length) {
						$(c).children('div.content').slideDown({ duration: o.expandSpeed, easing: o.expandEasing });
					} else {
						$(target).children('div.content').slideUp({ duration: o.collapseSpeed, easing: o.collapseEasing });
					}
					return false;
				}
				function bindTree(t) {
					$(t).find('span.image').unbind(o.folderEvent);
					$(t).find('span.image').bind(o.folderEvent, function() {
						return clickExpand($(this).parent());
					});
					$(t).find('a.content').unbind(o.folderEvent);
					$(t).find('a.content').bind(o.folderEvent, function() {
						return clickLoad($(this).parent());
					});
				}
				bindTree(this);
			});
		}
	});
	
})(jQuery);
