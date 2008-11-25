/**
 * js/jQuery.extensions
 * ~~~~~~~~~~~~~~~~~~~~
 *
 * Various small jQuery extensions.
 *
 * :copyright: 2008 by Armin Ronacher.
 * :license: GNU GPL.
 */


/**
 * Fetch all the nodes until a new node is found.
 */
jQuery.fn.nextUntil = function(expr) {
  var match = [];
  this.each(function() {
    for (var i = this.nextSibling; i; i = i.nextSibling)
      if (i.nodeType == 1) {
        if (jQuery.filter(expr, [i]).r.length)
          break;
        match.push(i);
      }
  });
  return this.pushStack(match, arguments);
};

/**
 * Fetch all the nodes as long as a new node is found.
 */
jQuery.fn.nextWhile = function(expr) {
  var match = [];
  this.each(function() {
    for (var i = this.nextSibling; i; i = i.nextSibling)
      if (i.nodeType == 1) {
        if (!jQuery.filter(expr, [i]).r.length)
          break;
        match.push(i);
      }
  });
  return this.pushStack(match, arguments);
};

/**
 * add the current node to the list
 */
jQuery.fn.andSelf = function() {
  return this.add(this.prevObject);
};
