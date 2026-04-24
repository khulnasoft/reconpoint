/**
 * Central namespace for window keys used with one-shot console warnings.
 * Load before `reconpoint_datatable_port_endpoint_pure.js`, `port_display.js`, and
 * `datatables/renderers_subdomain_endpoint.js` (see `base.html`).
 * Add new keys here with a unique prefix; read from `RECONPOINT_CONSOLE_WARN_KEYS` in each module.
 */
var RECONPOINT_CONSOLE_WARN_KEYS = {
    portDisplay: {
        missingServicesForRequestPort: "__reconpointWarnOnce_portDisplay_missingServicesForRequestPort",
        malformedUrlModalIp: "__reconpointWarnOnce_portDisplay_malformedUrlModalIp",
        malformedUrlModalSubdomainHttpUrl: "__reconpointWarnOnce_portDisplay_malformedUrlModalSubHttpUrl",
        malformedUrlNameColumn: "__reconpointWarnOnce_portDisplay_malformedUrlNameColumn"
    },
    rendererEndpoint: {
        missingEndpointDefaultsByPort: "__reconpointWarnOnce_rendererEndpoint_missingEdbp",
        invalidEndpointDefaultsByPort: "__reconpointWarnOnce_rendererEndpoint_invalidEdbp"
    }
};
