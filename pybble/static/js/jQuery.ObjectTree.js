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
// Usage: $('.fileTreeDemo').objTree( options, callback )
//
// Options:  root           - root folder to display; default = /
//           script         - location of the serverside AJAX file to use; for pybble, use /snippet/owner|parent|superparent
//           folderEvent    - event to trigger expand/collapse; default = click
//           expandSpeed    - default = 500 (ms); use -1 for no animation
//           collapseSpeed  - default = 500 (ms); use -1 for no animation
//           expandEasing   - easing function to use on expand (optional)
//           collapseEasing - easing function to use on collapse (optional)
//           multiFolder    - whether or not to limit the browser to one subfolder at a time
//           loadMessage    - Message to display while initial tree loads (can be HTML)
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
		objTree: function(o) {
			// Defaults
			if( !o ) var o = {};
			if( o.root == undefined ) o.root = '/';
			if( o.script == undefined ) o.script = 'jqueryFileTree.php';
			if( o.folderEvent == undefined ) o.folderEvent = 'click';
			if( o.expandSpeed == undefined ) o.expandSpeed= 500;
			if( o.collapseSpeed == undefined ) o.collapseSpeed= 500;
			if( o.expandEasing == undefined ) o.expandEasing = null;
			if( o.collapseEasing == undefined ) o.collapseEasing = null;
			if( o.multiFolder == undefined ) o.multiFolder = true;
			if( o.loadMessage == undefined ) o.loadMessage = 'Loading...';
			
			$(this).each( function() {
				
				function showTree(c, t) {
					$(c).addClass('wait');
					$.get(o.script+'/'+t, function(data) {
						data = $(data)
						$(c).replaceWith(data)
						c = data
						// if( o.root == t ) $(c).find('UL:hidden').show(); else $(c).find('UL:hidden').slideDown({ duration: o.expandSpeed, easing: o.expandEasing });
						$(c).find('UL:hidden').show();
						bindTree(c);
					});
				}
				function clickExpand(target) {
					if( $(target).hasClass('directory') ) {
						if( $(target).hasClass('collapsed') ) {
							// Expand
							if( !o.multiFolder ) {
								$(target).parent().find('UL').slideUp({ duration: o.collapseSpeed, easing: o.collapseEasing });
								$(target).parent().find('LI.directory').removeClass('expanded').addClass('collapsed');
							}
							$(target).find('UL').remove(); // cleanup
							showTree( $(target), escape($(target).attr('rel') ));
							$(target).removeClass('collapsed').addClass('expanded');
						} else {
							// Collapse
							// $(target).find('UL').slideUp({ duration: o.collapseSpeed, easing: o.collapseEasing });
							$(target).find('UL').hide();
							$(target).removeClass('expanded').addClass('collapsed');
						}
					}
					return false;
				}
				function bindTree(t) {
					$(t).find('span.image').bind(o.folderEvent, function() {
						clickExpand($(this).parent())
					});
				}
				// Loading message
				$(this).html('<li class="wait"><span class="image" />' + o.loadMessage + '</li>');
				// Get the initial file list
				showTree( $(this).find('LI'), escape(o.root) );
			});
		}
	});
	
})(jQuery);
