/**
 * Safe tooltip init: dispose any existing Bootstrap tooltip on the elements before (re)initialising.
 * Use in drawCallback and on page init to avoid "Bootstrap doesn't allow more than one instance per element".
 */
(function (window) {
  "use strict";

  const disposeTooltips = function ($el) {
    if (!$el || !$el.length) return;
    $el.each(function () {
      try {
        window.jQuery(this).tooltip("dispose");
      } catch (e) {
        // no-op if no tooltip was bound
      }
    });
  };

  /**
   * @param {string|jQuery} selectorOrJq - CSS selector or jQuery collection
   * @param {object} [options] - Bootstrap tooltip options (template, etc.)
   */
  const reconpointSafeTooltipInit = function (selectorOrJq, options) {
    const $ = window.jQuery;
    if (typeof $ === "undefined") return;
    const $el = typeof selectorOrJq === "string" ? $(selectorOrJq) : selectorOrJq;
    if (!$el || !$el.length) return;
    disposeTooltips($el);
    $el.tooltip(options || {});
  };

  /**
   * Returns a drawCallback function that initialises tooltips on the table body.
   * Use in DataTables config to avoid duplicating drawCallback logic across templates.
   * @param {string} tableSelector - CSS selector for the table (e.g. '#scan_history_table').
   * @param {object} [options] - Optional. tooltipTemplate: custom Bootstrap tooltip template string.
   * @returns {function} drawCallback(settings) that runs reconpointSafeTooltipInit on .badge, .bs-tooltip, [data-toggle="tooltip"].
   */
  const getReconpointDatatableDrawCallbackTooltips = function (tableSelector, options) {
    const opts = options || {};
    const tooltipTemplate = opts.tooltipTemplate;
    return function (settings) {
      if (typeof window.reconpointSafeTooltipInit !== "function") return;
      const $ = window.jQuery;
      if (typeof $ === "undefined") return;
      const $table = $(tableSelector);
      if (!$table.length) return;
      const $body = $table.closest(".dataTables_wrapper").find(".dataTables_scrollBody").length
        ? $table.closest(".dataTables_wrapper").find(".dataTables_scrollBody")
        : $table;
      const templateOpts = tooltipTemplate
        ? { template: tooltipTemplate }
        : { template: '<div class="tooltip status" role="tooltip"><div class="arrow"></div><div class="tooltip-inner"></div></div>' };
      window.reconpointSafeTooltipInit($body.find(".badge"), templateOpts);
      window.reconpointSafeTooltipInit($body.find(".bs-tooltip"), templateOpts);
      window.reconpointSafeTooltipInit($body.find('[data-toggle="tooltip"]'), templateOpts);
    };
  };

  window.reconpointSafeTooltipInit = reconpointSafeTooltipInit;
  window.getReconpointDatatableDrawCallbackTooltips = getReconpointDatatableDrawCallbackTooltips;
})(window);
