/**
 * DataTables layout and scroller options (page length, length menu, scroller).
 * Use getReconpointDatatableLayoutFull() and getReconpointDatatableScrollerOptions() when initialising
 * server-side DataTables so they respect the Interface > DataTables display setting.
 */
(function (window) {
  "use strict";

  const useScroller = function () {
    return Boolean(window.RECONPOINT_DATATABLE_USE_SCROLLER);
  };

  const getReconpointDatatableLayoutFull = function () {
    if (useScroller() && window.RECONPOINT_DATATABLE_LAYOUT_FULL_SCROLLER) {
      return window.RECONPOINT_DATATABLE_LAYOUT_FULL_SCROLLER;
    }
    return window.RECONPOINT_DATATABLE_LAYOUT_FULL_CLASSIC || window.RECONPOINT_DATATABLE_LAYOUT_FULL;
  };

  const hasScrollerPlugin = function () {
    return (
      typeof window.jQuery !== "undefined" &&
      typeof window.jQuery.fn !== "undefined" &&
      typeof window.jQuery.fn.DataTable !== "undefined" &&
      typeof window.jQuery.fn.DataTable.Scroller !== "undefined"
    );
  };

  const getReconpointDatatableScrollerOptions = function (scrollY) {
    if (!useScroller()) return {};
    if (!hasScrollerPlugin()) {
      if (window.console && typeof window.console.warn === "function") {
        window.console.warn(
          "[DataTables] Scroller mode requested (RECONPOINT_DATATABLE_USE_SCROLLER=true) " +
            "but DataTables Scroller plugin is not loaded. Falling back to classic layout."
        );
      }
      return {};
    }
    const height = typeof scrollY === "string" ? scrollY : "60vh";
    return { scrollY: height, deferRender: true, scroller: true };
  };

  const PAGE_LENGTH_STORAGE_KEY_PREFIX = "reconpoint-datatable-pageLength-";

  const getDefaultPageLength = function () {
    const n = window.RECONPOINT_DATATABLE_PAGE_LENGTH;
    return typeof n === "number" && n > 0 ? n : 30;
  };

  /**
   * Returns the page length to use for a DataTable. If tableId is given, uses the user's
   * saved value for that table (if valid and in length menu), otherwise the global default.
   *
   * @param {string} [tableId] - Optional table identifier (e.g. from the table's id attribute).
   * @returns {number} Page length to use.
   */
  const getReconpointDatatablePageLength = function (tableId) {
    const defaultLen = getDefaultPageLength();
    if (!tableId || typeof window.localStorage === "undefined") {
      return defaultLen;
    }
    try {
      const key = PAGE_LENGTH_STORAGE_KEY_PREFIX + String(tableId);
      const stored = window.localStorage.getItem(key);
      if (stored === null) return defaultLen;
      const parsed = parseInt(stored, 10);
      if (Number.isNaN(parsed)) return defaultLen;
      const pair = getReconpointDatatableLengthMenu();
      const allowed = Array.isArray(pair[0]) ? pair[0] : [10, 20, 30, 50, 100, 200, 500, 1000, -1];
      if (allowed.indexOf(parsed) === -1) return defaultLen;
      return parsed;
    } catch (e) {
      return defaultLen;
    }
  };

  /**
   * Saves the user's page length choice for a table. Call when the length menu changes.
   *
   * @param {string} tableId - Table identifier (must match the id used in getReconpointDatatablePageLength).
   * @param {number} value - Selected page length (e.g. -1 for "All").
   */
  const setReconpointDatatablePageLength = function (tableId, value) {
    if (!tableId || typeof window.localStorage === "undefined") return;
    try {
      const key = PAGE_LENGTH_STORAGE_KEY_PREFIX + String(tableId);
      window.localStorage.setItem(key, String(value));
    } catch (e) {
      // ignore storage errors
    }
  };

  const getReconpointDatatableLengthMenu = function () {
    const values = window.RECONPOINT_DATATABLE_LENGTH_MENU_VALUES;
    const arr = Array.isArray(values) ? values : [10, 20, 30, 50, 100, 200, 500, 1000, -1];
    const labels = arr.map(function (v) { return v === -1 ? "All" : String(v); });
    return [arr, labels];
  };

  window.getReconpointDatatableLayoutFull = getReconpointDatatableLayoutFull;
  window.getReconpointDatatableScrollerOptions = getReconpointDatatableScrollerOptions;
  window.getReconpointDatatablePageLength = getReconpointDatatablePageLength;
  window.setReconpointDatatablePageLength = setReconpointDatatablePageLength;
  window.getReconpointDatatableLengthMenu = getReconpointDatatableLengthMenu;

  if (window.RECONPOINT_DATATABLE_USE_SCROLLER && !hasScrollerPlugin() && (window.console && typeof window.console.warn === "function")) {
        window.console.warn(
          "[DataTables] Scroller mode is enabled (RECONPOINT_DATATABLE_USE_SCROLLER=true) " +
            "but the DataTables Scroller plugin is not loaded. Tables will use classic layout. " +
            "Load the Scroller extension or disable Scroller in Interface settings."
        );
  }
})(window);
