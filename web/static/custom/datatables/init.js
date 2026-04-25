/**
 * DataTables init: getReconpointDatatableConfig, initServerSideDataTable, initReconpointServerSideDataTable,
 * initDetailScanServerSideTable, initClientSideDataTable.
 *
 * Depends on: layout.js (getReconpointDatatableScrollerOptions, getReconpointDatatableLayoutFull, lengthMenu, pageLength),
 * filters.js (buildDatatableFilterPayload, getReconpointDatatableFilterParams), rowgroup.js (getReconpointRowGroupInitialState,
 * attachReconpointDatatableRowGroupSelector), columns.js (getReconpointDatatableOrderFromNames), tooltips.js (getReconpointDatatableDrawCallbackTooltips).
 * Requires: window.jQuery and jQuery.fn.DataTable. If these are missing, init helpers no-op and log a warning.
 * reconpointApplyImportantRowHighlight uses window.reconpointIsImportant from custom.js (load custom.js before this file).
 * Backend mapping: filterParamsElId / filterSelectToParam come from FILTER_CONTEXT_* (filters.py); buildDatatableFilterPayload
 * sends selected values as API params. See README "Backend → frontend mapping".
 */
(function (window) {
  "use strict";

  if (typeof window.buildDatatableFilterPayload !== "function") {
    window.buildDatatableFilterPayload = function () { return {}; };
  }
  if (typeof window.attachDatatableFilters !== "function") {
    window.attachDatatableFilters = function () {};
  }

  const requireDataTableGlobals = function () {
    const $ = window.jQuery;
    if (!$ || typeof $.fn !== "object" || typeof $.fn.DataTable !== "function") {
      if (typeof console !== "undefined" && console.warn) {
        console.warn("reconpoint DataTables init: jQuery or DataTable plugin not loaded. Ensure script order: jQuery, DataTables, then datatables/*.js.");
      }
      return false;
    }
    const hasLayout = typeof window.getReconpointDatatableLayoutFull === "function" || (window.RECONPOINT_DATATABLE_LAYOUT_FULL != null);
    if (!hasLayout && typeof console !== "undefined" && console.warn) {
      console.warn("reconpoint DataTables init: getReconpointDatatableLayoutFull / RECONPOINT_DATATABLE_LAYOUT_FULL missing. Load layout.js before init.js.");
    }
    return true;
  };

  const tableIdFromSelector = function (selector) {
    if (!selector || typeof selector !== "string") return null;
    const s = selector.trim().replace(/^#/, "");
    return s.length > 0 ? s : null;
  };

  const getCurrentProjectSlug = function () {
    if (typeof window.getCurrentProjectSlug === "function") {
      return window.getCurrentProjectSlug() || "";
    }
    if (typeof document === "undefined" || !document.body) return "";
    return (document.body.getAttribute("data-project-slug") || "").trim();
  };

  const getProjectScopedStorageKey = function (baseKey, tableId) {
    if (!tableId) return null;
    const projectSlug = getCurrentProjectSlug();
    const suffix = projectSlug ? ":" + projectSlug : "";
    return baseKey + "-" + tableId + suffix;
  };

  const getPersistedQuickSearchState = function (tableId) {
    const storage = window.reconpointStorage;
    const storageKey = getProjectScopedStorageKey("reconpoint-datatable-search", tableId);
    if (!storageKey || !storage || typeof storage.getJson !== "function") return "";
    try {
      const persistedSearch = storage.getJson(storageKey);
      return typeof persistedSearch === "string" ? persistedSearch : "";
    } catch (e) {
      return "";
    }
  };

  const getPersistedColumnSearchState = function (tableId) {
    const storage = window.reconpointStorage;
    const storageKey = getProjectScopedStorageKey("reconpoint-datatable-columnSearch", tableId);
    if (!storageKey || !storage || typeof storage.getJson !== "function") return {};
    try {
      const persisted = storage.getJson(storageKey);
      return persisted && typeof persisted === "object" && !Array.isArray(persisted) ? persisted : {};
    } catch (e) {
      return {};
    }
  };

  const buildInitialDatatableState = function (tableId, filterSelectToParam) {
    const filterIds = filterSelectToParam ? Object.keys(filterSelectToParam) : [];
    const readFilters = typeof window.getPersistedDatatableFilterState === "function"
      ? window.getPersistedDatatableFilterState
      : function () { return {}; };
    return {
      filters: readFilters(tableId, filterIds),
      quickSearch: getPersistedQuickSearchState(tableId),
      columnSearch: getPersistedColumnSearchState(tableId),
    };
  };

  const buildFilterPayloadFromState = function (filterSelectToParam, persistedState) {
    if (!filterSelectToParam || typeof filterSelectToParam !== "object") return {};
    const payload = {};
    Object.keys(filterSelectToParam).forEach(function (selectId) {
      const paramName = filterSelectToParam[selectId];
      if (!paramName || typeof paramName !== "string") return;
      const selected = persistedState && persistedState[selectId];
      if (Array.isArray(selected) && selected.length > 0) {
        payload[paramName] = selected.slice();
      }
    });
    return payload;
  };

  const getReconpointDatatableConfig = function (tableSelector, options) {
    const opts = options || {};
    const tableId = tableIdFromSelector(tableSelector);
    const scrollY = opts.scrollY || "60vh";
    const scrollerOpts =
      typeof window.getReconpointDatatableScrollerOptions === "function"
        ? window.getReconpointDatatableScrollerOptions(scrollY)
        : {};
    const pageLength =
      typeof window.getReconpointDatatablePageLength === "function"
        ? window.getReconpointDatatablePageLength(tableId)
        : 30;
    const baseOptions = {
      serverSide: true,
      processing: true,
      responsive: true,
      ajax: Object.assign({ dataSrc: "data" }, opts.ajax || {}),
      layout:
        typeof window.getReconpointDatatableLayoutFull === "function"
          ? window.getReconpointDatatableLayoutFull()
          : window.RECONPOINT_DATATABLE_LAYOUT_FULL,
      lengthMenu:
        typeof window.getReconpointDatatableLengthMenu === "function"
          ? window.getReconpointDatatableLengthMenu()
          : [[10, 20, 30, 50, 100, 200, 500, 1000, -1], ["10", "20", "30", "50", "100", "200", "500", "1000", "All"]],
      pageLength: pageLength
    };
    const merged = Object.assign({}, baseOptions, scrollerOpts, opts);
    if (merged.ajax && merged.ajax.dataSrc === undefined) merged.ajax.dataSrc = "data";
    merged.__reconpointDatatableConfig = true;
    return merged;
  };

  const initServerSideDataTable = function (tableSelector, options) {
    if (!requireDataTableGlobals()) return null;
    const merged =
      options && options.__reconpointDatatableConfig
        ? options
        : getReconpointDatatableConfig(tableSelector, options);
    const userInitComplete = merged.initComplete;
    merged.initComplete = function () {
      if (typeof window.reconpointSafeTooltipInit === "function") {
        window.reconpointSafeTooltipInit(
          "[data-toggle=\"tooltip\"]:not([data-bs-toggle=\"dropdown\"]):not([data-toggle=\"dropdown\"])"
        );
      }
      if (typeof userInitComplete === "function") userInitComplete.apply(this, arguments);
    };
    const table = window.jQuery(tableSelector).DataTable(merged);
    const tableId = tableIdFromSelector(tableSelector);
    if (tableId && typeof window.setReconpointDatatablePageLength === "function") {
      table.on("length.dt", function (_e, _settings, len) {
        window.setReconpointDatatablePageLength(tableId, len);
      });
    }
    return table;
  };

  /**
   * One-call server-side DataTable init with optional filter payload, drawCallback tooltips, and row group.
   * Templates pass a single config; this wrapper merges filter data, sets drawCallback, inits the table, then attaches row group if requested.
   * When rowGroup has cookieKey and rowGroupBaseOpts, initial order/rowGroup are computed from cookie via getReconpointRowGroupInitialState.
   *
   * @param {string} tableSelector - CSS selector for the table (e.g. '#scan_history_table').
   * @param {object} options - getReconpointDatatableConfig options plus:
   *   - filterSelectToParam: optional object (select id -> param name); merged into ajax.data via buildDatatableFilterPayload.
   *   - filterParamsElId: optional; if set and filterSelectToParam not set, filterSelectToParam = getReconpointDatatableFilterParams(filterParamsElId).
   *   - drawCallbackTooltips: optional true or { tooltipTemplate: '...' }; sets drawCallback to getReconpointDatatableDrawCallbackTooltips.
   *   - rowGroup: optional { selector, groups, columns, defaultOrderWhenDisabled, snackbarMessage, storageKey, cookieKey, initialGroupFromCookie } or with rowGroupBaseOpts to auto-compute initial state from storage.
   *   - orderFromColumns: optional [columns, defaultOrder] for getReconpointDatatableOrderFromNames; used when order not set.
   * @returns {DataTable.Api} The DataTable API instance.
   */
  const initReconpointServerSideDataTable = function (tableSelector, options) {
    if (!requireDataTableGlobals()) return null;
    const opts = options
      ? Object.assign({}, options, { ajax: options.ajax ? Object.assign({}, options.ajax) : options.ajax })
      : {};
    let filterSelectToParam = opts.filterSelectToParam || null;
    if (!filterSelectToParam && opts.filterParamsElId && typeof window.getReconpointDatatableFilterParams === "function") {
      filterSelectToParam = window.getReconpointDatatableFilterParams(opts.filterParamsElId);
    }
    const drawCallbackTooltips = opts.drawCallbackTooltips;
    const rowGroup = opts.rowGroup;
    const orderFromColumns = opts.orderFromColumns;
    const tableId = tableIdFromSelector(tableSelector);
    const singleDrawInitialState =
      opts.singleDrawInitialState !== false
      && !!filterSelectToParam
      && !!tableId;
    const initialState = singleDrawInitialState ? buildInitialDatatableState(tableId, filterSelectToParam) : null;
    if (singleDrawInitialState && initialState && initialState.quickSearch) {
      opts.search = Object.assign({}, opts.search || {}, { search: initialState.quickSearch });
    }
    if (
      singleDrawInitialState
      && initialState
      && initialState.columnSearch
      && opts.columns
      && Array.isArray(opts.columns)
      && Object.keys(initialState.columnSearch).length > 0
    ) {
      opts.columns = opts.columns.map(function (columnDef, idx) {
        const copy = Object.assign({}, columnDef || {});
        const stored = initialState.columnSearch[idx];
        if (stored != null && String(stored) !== "") {
          copy.search = Object.assign({}, copy.search || {}, { value: String(stored) });
        }
        return copy;
      });
    }

    let initialFilterPayloadApplied = false;
    if (opts.ajax && filterSelectToParam && typeof window.buildDatatableFilterPayload === "function") {
      const baseData = opts.ajax.data;
      let firstRequest = true;
      const initialFilterPayload =
        singleDrawInitialState && initialState && initialState.filters
          ? buildFilterPayloadFromState(filterSelectToParam, initialState.filters)
          : {};
      initialFilterPayloadApplied = Object.keys(initialFilterPayload).length > 0;
      opts.ajax = Object.assign({}, opts.ajax, {
        data: function (d) {
          if (typeof baseData === "function") {
            const baseResult = baseData(d);
            if (baseResult && typeof baseResult === "object") {
              Object.assign(d, baseResult);
            }
          } else if (baseData) {
            Object.assign(d, baseData);
          }
          if (singleDrawInitialState && firstRequest && initialFilterPayloadApplied) {
            Object.assign(d, initialFilterPayload);
            firstRequest = false;
            return;
          }
          Object.assign(d, window.buildDatatableFilterPayload(filterSelectToParam));
        },
      });
    }

    if (drawCallbackTooltips && typeof window.getReconpointDatatableDrawCallbackTooltips === "function") {
      const tooltipOpts = drawCallbackTooltips === true ? {} : drawCallbackTooltips;
      const userDrawCallback = opts.drawCallback;
      const tooltipDrawCallback = window.getReconpointDatatableDrawCallbackTooltips(tableSelector, tooltipOpts);
      opts.drawCallback = function (settings) {
        if (typeof tooltipDrawCallback === "function") tooltipDrawCallback.call(this, settings);
        if (typeof userDrawCallback === "function") userDrawCallback.apply(this, arguments);
      };
    }

    let rowGroupAttachOpts = rowGroup;
    if (rowGroup && rowGroup.cookieKey && rowGroup.rowGroupBaseOpts && typeof window.getReconpointRowGroupInitialState === "function") {
      const cols = rowGroup.columns || [];
      const defaultOrder = rowGroup.defaultOrderWhenDisabled || [["id", "desc"]];
      const state = window.getReconpointRowGroupInitialState(
        rowGroup.cookieKey,
        rowGroup.groups || [],
        defaultOrder,
        cols,
        rowGroup.rowGroupBaseOpts
      );
      opts.order = state.order;
      opts.rowGroup = state.rowGroup;
      rowGroupAttachOpts = Object.assign({}, rowGroup, {
        storageKey: rowGroup.cookieKey,
        initialGroupFromCookie: state.appliedFromStorage
      });
    } else if (orderFromColumns && opts.order === undefined) {
      const cols = orderFromColumns[0];
      const defaultOrder = orderFromColumns[1] || [["id", "desc"]];
      opts.order =
        typeof window.getReconpointDatatableOrderFromNames === "function"
          ? window.getReconpointDatatableOrderFromNames(cols, defaultOrder)
          : defaultOrder;
    }

    const table = initServerSideDataTable(tableSelector, opts);
    if (table && singleDrawInitialState) {
      table._reconpointInitialStateApplied = true;
      table._reconpointInitialState = initialState || {};
      table._reconpointInitialFilterPayloadApplied = initialFilterPayloadApplied;
    }

    if (rowGroupAttachOpts && typeof window.attachReconpointDatatableRowGroupSelector === "function") {
      window.attachReconpointDatatableRowGroupSelector(table, rowGroupAttachOpts);
    }

    return table;
  };

  const initClientSideDataTable = function (tableSelector, extraOptions) {
    if (!requireDataTableGlobals()) return null;
    const opts = extraOptions || {};
    const scrollY = opts.scrollY || "60vh";
    const scrollerOpts =
      typeof window.getReconpointDatatableScrollerOptions === "function"
        ? window.getReconpointDatatableScrollerOptions(scrollY)
        : {};
    const baseOptions = {
      layout: window.RECONPOINT_DATATABLE_LAYOUT_WITH_SEARCH,
      lengthMenu:
        typeof window.getReconpointDatatableLengthMenu === "function"
          ? window.getReconpointDatatableLengthMenu()
          : [[30, 50, 100, -1], ["30", "50", "100", "All"]],
      pageLength:
        typeof window.getReconpointDatatablePageLength === "function"
          ? window.getReconpointDatatablePageLength()
          : 30,
      initComplete: function () {
        if (typeof window.reconpointSafeTooltipInit === "function") {
          window.reconpointSafeTooltipInit(
            "[data-toggle=\"tooltip\"]:not([data-bs-toggle=\"dropdown\"]):not([data-toggle=\"dropdown\"])"
          );
        }
      }
    };
    const merged = Object.assign({}, baseOptions, scrollerOpts, opts);
    return window.jQuery(tableSelector).DataTable(merged);
  };

  /**
   * Detail-scan style server-side DataTable: same as initReconpointServerSideDataTable but with
   * default scroll (60vh), layout, and drawCallback tooltips so per-table configs stay short.
   * Use for endpoint/subdomain/change tables that share ajax + tooltips + optional row group.
   *
   * @param {string} tableSelector - CSS selector for the table (e.g. '#table-subdomain-changes').
   * @param {object} options - Options for initReconpointServerSideDataTable. drawCallbackTooltips
   *   defaults to true; scrollY defaults to "60vh". Pass columns, ajax, order, drawCallback, etc.
   * @returns {DataTable.Api} The DataTable API instance.
   */
  const initDetailScanServerSideTable = function (tableSelector, options) {
    if (!requireDataTableGlobals()) return null;
    const opts = options ? Object.assign({}, options) : {};
    const scrollY = opts.scrollY != null ? opts.scrollY : "60vh";
    const scrollerOpts =
      typeof window.getReconpointDatatableScrollerOptions === "function"
        ? window.getReconpointDatatableScrollerOptions(scrollY)
        : {};
    const layout =
      typeof window.getReconpointDatatableLayoutFull === "function"
        ? window.getReconpointDatatableLayoutFull()
        : window.RECONPOINT_DATATABLE_LAYOUT_FULL;
    if (opts.drawCallbackTooltips === undefined) opts.drawCallbackTooltips = true;
    const merged = Object.assign({}, scrollerOpts, { layout: layout }, opts);
    return initReconpointServerSideDataTable(tableSelector, merged);
  };

  window.getReconpointDatatableConfig = getReconpointDatatableConfig;
  window.initServerSideDataTable = initServerSideDataTable;
  window.initReconpointServerSideDataTable = initReconpointServerSideDataTable;
  window.initDetailScanServerSideTable = initDetailScanServerSideTable;
  window.initClientSideDataTable = initClientSideDataTable;

  /**
   * Attach a simple global search input to a DataTable instance and place it to the right
   * of the "Results" (length) dropdown in the table's control row.
   * opts: { inputSelector: '#input-id', delayMs?: number, tableId?: string }
   */
  window.attachDatatableQuickSearch = function (table, opts) {
    if (!table || !opts || !opts.inputSelector) {
      return;
    }
    const $ = window.jQuery;
    if (!$) {
      return;
    }
    const $input = $(opts.inputSelector);
    if (!$input.length) {
      return;
    }
    const delay = typeof opts.delayMs === "number" ? opts.delayMs : 700;
    const restoreOnInit = opts.restoreOnInit !== false;
    const storage = window.reconpointStorage;
    const dtTable = typeof table.table === "function" ? table.table() : null;
    const derivedId =
      dtTable && typeof dtTable.node === "function" ? dtTable.node().id : null;
    const tableId = opts.tableId || derivedId;
    const storageKey = getProjectScopedStorageKey("reconpoint-datatable-search", tableId);

    const hasPreloadedState = table && table._reconpointInitialStateApplied === true;
    if (restoreOnInit && storage && typeof storage.getJson === "function" && storageKey) {
      try {
        const persistedSearch = storage.getJson(storageKey);
        if (typeof persistedSearch === "string" && persistedSearch.length > 0) {
          $input.val(persistedSearch);
          if (!hasPreloadedState && table.search() !== persistedSearch) {
            table.search(persistedSearch);
            table._reconpointNeedsInitialSearchDraw = true;
          }
        }
      } catch (e) {
        // ignore storage errors
      }
    }
    let timeoutId = null;
    const triggerSearch = function () {
      const val = $input.val() || "";
      if (table.search() !== val) {
        table.search(val).draw();
        if (storageKey && storage && typeof storage.setJson === "function") {
          storage.setJson(storageKey, val);
        }
      }
    };
    $input.off(".reconpointQuickSearch").on("keyup.reconpointQuickSearch change.reconpointQuickSearch", function () {
      if (timeoutId !== null) {
        window.clearTimeout(timeoutId);
      }
      timeoutId = window.setTimeout(function () {
        timeoutId = null;
        triggerSearch();
      }, delay);
    });

    if (table.table && typeof table.table === "function") {
      const container = table.table().container();
      if (container) {
        const $container = $(container);
        const $length = $container.find(".dt-length").first();
        if ($length.length) {
          const $searchBlock = $input.closest("div");
          if ($searchBlock.length && !$searchBlock.closest(".dt-container").length) {
            $length.after($searchBlock);
          }
        }
      }
    }

    // restored above via storage.getJson when available
    if (hasPreloadedState) {
      table._reconpointNeedsInitialSearchDraw = false;
      return;
    }
    if (table._reconpointNeedsInitialSearchDraw) {
      window.setTimeout(function () {
        if (table._reconpointNeedsInitialSearchDraw) {
          table._reconpointNeedsInitialSearchDraw = false;
          table.draw();
        }
      }, 0);
    }
  };

  /**
   * Attach per-column search inputs (header and/or footer) to a DataTable instance.
   *
   * Inputs must live inside the table header/footer and carry a data-column-index attribute:
   *   <input type="text" class="form-control form-control-sm datatable-column-search"
   *          data-column-index="2" placeholder="Search target">
   *
   * With scrollY, DataTables may move thead/tfoot into scroll containers; we resolve them
   * from the table's container so handlers attach to the correct nodes.
   *
   * opts: { tableSelector: '#table-id', delayMs?: number, tableId?: string }
   */
  window.attachDatatableColumnSearch = function (table, opts) {
    if (!table || !opts || !opts.tableSelector) {
      return;
    }
    const $ = window.jQuery;
    if (!$) {
      return;
    }
    const delay = typeof opts.delayMs === "number" ? opts.delayMs : 700;
    const restoreOnInit = opts.restoreOnInit !== false;
    const storage = window.reconpointStorage;
    const explicitTableId = opts.tableId;
    const derivedTableId =
      table.table && typeof table.table === "function" && table.table().node && table.table().node().id
        ? table.table().node().id
        : null;
    const tableId = explicitTableId || derivedTableId;
    const storageKey = getProjectScopedStorageKey("reconpoint-datatable-columnSearch", tableId);
    const $table = $(opts.tableSelector);
    if (!$table.length) {
      return;
    }

    // Resolve thead/tfoot from the DataTable container so we find them even when
    // scrollY has moved them into .dataTables_scrollHead / .dataTables_scrollFoot.
    let $thead = $table.find("thead");
    let $tfoot = $table.find("tfoot");
    if (table.table && typeof table.table === "function") {
      const container = table.table().container();
      if (container && $(container).length) {
        const $wrapper = $(container);
        if (!$thead.length) {
          $thead = $wrapper.find(".dataTables_scrollHead thead, thead");
        }
        if (!$tfoot.length) {
          $tfoot = $wrapper.find(".dataTables_scrollFoot tfoot, tfoot");
        }
      }
    }

    const debounce = function (fn, wait) {
      let timeoutId = null;
      return function debounced() {
        const ctx = this;
        const args = arguments;
        if (timeoutId !== null) {
          window.clearTimeout(timeoutId);
        }
        timeoutId = window.setTimeout(function () {
          timeoutId = null;
          fn.apply(ctx, args);
        }, wait);
      };
    };

    const hasPreloadedState = table && table._reconpointInitialStateApplied === true;
    const attachToInputs = function ($container, baseState) {
      if (!$container || !$container.length) {
        return;
      }
      $container
        .find("input.datatable-column-search[data-column-index], select.datatable-column-search[data-column-index]")
        .each(function () {
          const idxAttr = this.getAttribute("data-column-index");
          const colIdx = idxAttr != null ? parseInt(idxAttr, 10) : NaN;
          if (Number.isNaN(colIdx)) {
            return;
          }
          const handler = debounce(function () {
            const val = this.value || "";
            const current = table.column(colIdx).search();
            if (current !== val) {
              table.column(colIdx).search(val).draw();
              if (storageKey && storage && typeof storage.setJson === "function") {
                const nextState = Object.assign({}, baseState || {});
                if (val) {
                  nextState[colIdx] = val;
                } else {
                  delete nextState[colIdx];
                }
                storage.setJson(storageKey, nextState);
              }
            }
          }, delay);
          $(this).off(".reconpointColumnSearch").on("keyup.reconpointColumnSearch change.reconpointColumnSearch", handler);

          if (baseState && Object.prototype.hasOwnProperty.call(baseState, colIdx)) {
            const savedVal = baseState[colIdx];
            if (savedVal != null && savedVal !== "") {
              this.value = savedVal;
              const current = table.column(colIdx).search();
              if (!hasPreloadedState && current !== savedVal) {
                table.column(colIdx).search(savedVal);
              }
            }
          }
        });
    };

    let initialState = null;
    if (restoreOnInit && storageKey && storage && typeof storage.getJson === "function") {
      try {
        const stored = storage.getJson(storageKey);
        if (stored && typeof stored === "object") {
          initialState = stored;
        }
      } catch (e) {
        initialState = null;
      }
    }

    attachToInputs($thead, initialState);
    attachToInputs($tfoot, initialState);

    if (hasPreloadedState) {
      table._reconpointNeedsInitialSearchDraw = false;
      return;
    }
    if (initialState && Object.keys(initialState).length > 0) {
      table.draw();
      table._reconpointNeedsInitialSearchDraw = false;
      return;
    }
    if (table._reconpointNeedsInitialSearchDraw) {
      table._reconpointNeedsInitialSearchDraw = false;
      table.draw();
    }
  };

  /**
   * DataTables createdRow / rowCallback: sync table-danger from row data (subdomains, IPs, etc.).
   * Single entry point so reload and toggle stay aligned across tables.
   *
   * @param {HTMLTableRowElement} row
   * @param {object} data - Row payload from the server (expects is_important when applicable)
   */
  window.reconpointApplyImportantRowHighlight = function (row, data) {
    if (!row || !row.classList || data == null || typeof data !== "object") {
      return;
    }
    row.classList.toggle("table-danger", window.reconpointIsImportant(data.is_important));
  };

  /**
   * Set or clear the important-row highlight (optimistic toggle or server sync).
   * @param {HTMLTableRowElement} row
   * @param {boolean} isImportant
   */
  window.reconpointSetImportantRowHighlightState = function (row, isImportant) {
    if (!row || !row.classList) {
      return;
    }
    row.classList.toggle("table-danger", !!isImportant);
  };
})(window);
