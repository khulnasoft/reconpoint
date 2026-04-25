/**
 * Lazy initialization for the IP DataTable (scan detail and target summary).
 * Requires jQuery, DataTable, initServerSideDataTable, getReconpointDatatableConfig,
 * window.reconpointApplyImportantRowHighlight (init.js),
 * selection_helpers.js (createReconpointDatatableIdSelection), RECONPOINT_IP_DATATABLE_COLUMNS,
 * ReconpointDatatableColumnDefs.getScanIpTableColumnDefs, reconpointColumnByName (columns.js),
 * and global renderBadge (port_display.js).
 */
(function (window) {
  "use strict";

  let ipImportantOnlyActive = false;
  let savedIpSearchBeforeImportant = "";

  /**
   * @typedef {Object} DetailScanIpTableConfig
   * @property {string} [tableSelector]
   * @property {string} ajaxUrl
   * @property {number} scanHistoryId
   * @property {string} projectSlug
   * @property {string} getIpDetailsUrl
   * @property {string} querySubdomainsUrl
   * @property {string} listIPsUrl
   * @property {string} downloadFilename
   */

  /**
   * @param {DetailScanIpTableConfig} config
   * @returns {object|null} DataTables API instance, or null.
   */
  window.initDetailScanIpDataTable = function (config) {
    const $ = window.jQuery;
    const DataTableLib = window.DataTable;
    if (!$ || !config || !config.ajaxUrl) {
      return null;
    }
    const tableSelector = config.tableSelector || "#ip_scan_results";
    if (
      DataTableLib &&
      typeof DataTableLib.isDataTable === "function" &&
      DataTableLib.isDataTable(tableSelector)
    ) {
      return window.ipTable || null;
    }
    const ipColumns = window.RECONPOINT_IP_DATATABLE_COLUMNS || [];
    const defsFactory =
      window.ReconpointDatatableColumnDefs && window.ReconpointDatatableColumnDefs.getScanIpTableColumnDefs;
    if (!defsFactory || typeof window.initServerSideDataTable !== "function") {
      return null;
    }
    const columnDefs = defsFactory({
      getIpDetailsUrl: config.getIpDetailsUrl,
      querySubdomainsUrl: config.querySubdomainsUrl,
      scanHistoryId: config.scanHistoryId,
      domainId: config.domainId,
      listIPsUrl: config.listIPsUrl,
      projectSlug: config.projectSlug,
    });
    const order = window.getReconpointDatatableOrderFromNames
      ? window.getReconpointDatatableOrderFromNames(
          ipColumns,
          window.RECONPOINT_DATATABLE_IP_DEFAULT_ORDER || [["address", "asc"]],
        )
      : [[1, "asc"]];

    const ipSel =
      typeof window.createReconpointDatatableIdSelection === "function"
        ? window.createReconpointDatatableIdSelection({
            countBadgeId: "ip_selected_count",
            disabledWhenEmptyIds: ["download_selected_ips_btn", "initiate_selected_ips_subscan_btn"],
          })
        : null;
    const ipSelection = ipSel ? ipSel.ids : new Set();
    const updateIpSelectionUI = ipSel
      ? function () {
          ipSel.refresh();
        }
      : function () {
          const count = ipSelection.size;
          const countBadge = document.getElementById("ip_selected_count");
          if (countBadge) {
            countBadge.textContent = count > 0 ? count + " selected" : "";
            countBadge.style.display = count > 0 ? "" : "none";
          }
          const downloadBtn = document.getElementById("download_selected_ips_btn");
          if (downloadBtn) {
            downloadBtn.classList.toggle("disabled", count === 0);
          }
          const subscanBtn = document.getElementById("initiate_selected_ips_subscan_btn");
          if (subscanBtn) {
            subscanBtn.classList.toggle("disabled", count === 0);
          }
        };
    window.getSelectedIpIds = function () {
      return Array.from(ipSelection).filter(function (id) {
        return Number.isFinite(id) && id > 0;
      });
    };

    window.uncheckIps = function () {
      if (ipSel) {
        ipSel.clear({ rowCheckboxSelector: ".ip_checkbox", headCheckboxId: "head_ip_checkbox" });
      } else {
        ipSelection.clear();
        document.querySelectorAll(".ip_checkbox").forEach(function (cb) {
          cb.checked = false;
        });
        const head = document.getElementById("head_ip_checkbox");
        if (head) {
          head.checked = false;
        }
        updateIpSelectionUI();
      }
    };

    window.showIpEndpointsByAddress = function (address) {
      const safeAddress = address || "";
      $("#pills-endpoints-tab").trigger("click");
      $("#endpoints-search").val(safeAddress);
      $("#endpoints-search-button").trigger("click");
    };

    window.ipTable = window.initServerSideDataTable(
      tableSelector,
      window.getReconpointDatatableConfig(tableSelector, {
        destroy: true,
        responsive: true,
        order: order,
        columns: ipColumns,
        columnDefs: columnDefs,
        createdRow: function (row, data) {
          if (typeof window.reconpointApplyImportantRowHighlight === "function") {
            window.reconpointApplyImportantRowHighlight(row, data);
          }
        },
        drawCallback: function (settings) {
          if (window.getReconpointDatatableDrawCallbackTooltips) {
            const fn = window.getReconpointDatatableDrawCallbackTooltips(tableSelector, {
              tooltipTemplate:
                '<div class="tooltip status" role="tooltip"><div class="arrow"></div><div class="tooltip-inner"></div></div>',
            });
            if (typeof fn === "function") {
              fn.call(this, settings);
            }
          }
          if (typeof window.initPortsPopovers === "function") {
            window.initPortsPopovers(tableSelector);
          }
        },
        headerCallback: function (e) {
          e.getElementsByTagName("th")[0].innerHTML =
            '<div class="form-check ms-1 form-check-primary"><input type="checkbox" class="float-start form-check-input" id="head_ip_checkbox"><span class="new-control-indicator"></span><span style="visibility:hidden">c</span></div>';
        },
        serverSide: true,
        ajax: {
          url: config.ajaxUrl,
          dataSrc: "data",
        },
      }),
    );

    if (window.attachReconpointIpScanTableHandlers) {
      window.attachReconpointIpScanTableHandlers(tableSelector);
    }

    const ipTable = window.ipTable;

    $("#ips-search").on("keyup", function () {
      if (ipImportantOnlyActive) {
        ipImportantOnlyActive = false;
        $("#load_important_ip_table_btn").removeClass("active").attr("aria-pressed", "false");
      }
      ipTable.search(this.value).draw();
    });
    $("#ip-search-button").on("click", function () {
      if (ipImportantOnlyActive) {
        ipImportantOnlyActive = false;
        $("#load_important_ip_table_btn").removeClass("active").attr("aria-pressed", "false");
      }
      ipTable.search($("#ips-search").val()).draw();
    });
    $("#reload_ip_table_btn")
      .off("click.ipDtReload")
      .on("click.ipDtReload", function () {
        ipTable.ajax.reload();
      });
    $("#load_important_ip_table_btn")
      .off("click.ipDtImportant")
      .on("click.ipDtImportant", function () {
        const $btn = $(this);
        if (!ipImportantOnlyActive) {
          savedIpSearchBeforeImportant = ipTable.search();
          ipImportantOnlyActive = true;
          ipTable.search("is_important=true").draw();
          $("#ips-search").val("");
          $btn.addClass("active").attr("aria-pressed", "true");
        } else {
          ipImportantOnlyActive = false;
          ipTable.search(savedIpSearchBeforeImportant).draw();
          $("#ips-search").val(savedIpSearchBeforeImportant);
          $btn.removeClass("active").attr("aria-pressed", "false");
        }
      });
    $(tableSelector).on("change", ".ip_checkbox", function () {
      const id = Number(this.value);
      if (this.checked) {
        ipSelection.add(id);
      } else {
        ipSelection.delete(id);
      }
      updateIpSelectionUI();
    });
    $(tableSelector).on("change", "#head_ip_checkbox", function () {
      const checked = this.checked;
      document.querySelectorAll(".ip_checkbox").forEach(function (cb) {
        cb.checked = checked;
        const id = Number(cb.value);
        if (checked) {
          ipSelection.add(id);
        } else {
          ipSelection.delete(id);
        }
      });
      updateIpSelectionUI();
    });
    $("#download_selected_ips_btn").on("click", function (e) {
      e.preventDefault();
      if (ipSelection.size === 0) {
        return;
      }
      const rowsById = new Map();
      ipTable
        .rows({ search: "applied" })
        .data()
        .toArray()
        .forEach(function (row) {
          rowsById.set(Number(row.id), row);
        });
      const ips = Array.from(ipSelection)
        .map(function (id) {
          return rowsById.get(id);
        })
        .filter(Boolean)
        .map(function (row) {
          return row.address || "";
        })
        .filter(Boolean);
      if (!ips.length) {
        return;
      }
      const dlFn = window.download;
      if (typeof dlFn === "function") {
        dlFn(config.downloadFilename || "selected-ips.txt", ips.join("\n"));
      }
    });

    const rowGroupCols = ipColumns.map(function (c) {
      return { name: c.name };
    });
    if (window.attachReconpointDatatableRowGroupSelector) {
      window.attachReconpointDatatableRowGroupSelector(ipTable, {
        selector: 'input[name="grouping_ip_row"]',
        groups: window.RECONPOINT_DATATABLE_IP_ROW_GROUP_GROUPS || [],
        defaultOrderWhenDisabled: window.RECONPOINT_DATATABLE_IP_DEFAULT_ORDER || [["address", "asc"]],
        columns: rowGroupCols,
        snackbarMessage:
          typeof window.getReconpointRowGroupSnackbarMessage === "function"
            ? window.getReconpointRowGroupSnackbarMessage("Grouping cleared", "IPs grouped by {label}")
            : undefined,
      });
    }
    if (window.ReconpointAdvancedSearch && typeof window.ReconpointAdvancedSearch.registerDataTable === "function") {
      window.ReconpointAdvancedSearch.registerDataTable("ips", ipTable);
    }

    const colByName = function (name) {
      return window.reconpointColumnByName ? window.reconpointColumnByName(ipTable, name, ipColumns) : null;
    };
    $("input[name=ip_subdomains_filter_checkbox]").on("change", function () {
      const c = colByName("subdomain_names");
      if (c) {
        c.visible($(this).is(":checked"));
      }
    });
    $("input[name=ip_ports_filter_checkbox]").on("change", function () {
      const c = colByName("ports");
      if (c) {
        c.visible($(this).is(":checked"));
      }
    });
    $("input[name=ip_technologies_filter_checkbox]").on("change", function () {
      const c = colByName("technologies");
      if (c) {
        c.visible($(this).is(":checked"));
      }
    });
    $("input[name=ip_alive_filter_checkbox]").on("change", function () {
      const c = colByName("alive");
      if (c) {
        c.visible($(this).is(":checked"));
      }
    });
    $("input[name=ip_cdn_filter_checkbox]").on("change", function () {
      const c = colByName("is_cdn");
      if (c) {
        c.visible($(this).is(":checked"));
      }
    });

    return ipTable;
  };

  /**
   * Lazy-load IP DataTable when the IP tab is shown (scan detail or target summary).
   * @param {DetailScanIpTableConfig} config same as initDetailScanIpDataTable
   * @param {object} [opts]
   * @param {string} [opts.tabSelector]
   * @param {string} [opts.tabPaneId]
   * @param {boolean} [opts.registerShowIpEndpointsNav] set window.showIpEndpointsByAddress for scan detail
   */
  window.registerDetailScanLazyIpTab = function (config, opts) {
    const $ = window.jQuery;
    if (!$ || !config) {
      return;
    }
    const o = opts || {};
    const tabSelector = o.tabSelector || "#pills-ip-tab";
    const tabPaneId = o.tabPaneId || "ip-tab";
    const tableSelector = config.tableSelector || "#ip_scan_results";
    const DataTableLib = window.DataTable;

    window.uncheckIps = window.uncheckIps || function () {};

    if (o.registerShowIpEndpointsNav) {
      window.showIpEndpointsByAddress =
        window.showIpEndpointsByAddress ||
        function (address) {
          const safeAddress = address || "";
          $("#pills-endpoints-tab").trigger("click");
          $("#endpoints-search").val(safeAddress);
          $("#endpoints-search-button").trigger("click");
        };
    }

    const initDetailScanIpTableIfNeeded = function () {
      if (
        typeof DataTableLib !== "undefined" &&
        DataTableLib &&
        typeof DataTableLib.isDataTable === "function" &&
        DataTableLib.isDataTable(tableSelector)
      ) {
        return;
      }
      if (typeof window.initDetailScanIpDataTable === "function") {
        window.initDetailScanIpDataTable(config);
      }
    };

    $(tabSelector)
      .off("click.ipLazy")
      .on("click.ipLazy", initDetailScanIpTableIfNeeded);

    const ipTabPaneEl = document.getElementById(tabPaneId);
    if (ipTabPaneEl && ipTabPaneEl.classList.contains("active") && ipTabPaneEl.classList.contains("show")) {
      initDetailScanIpTableIfNeeded();
    }
  };
})(window);
