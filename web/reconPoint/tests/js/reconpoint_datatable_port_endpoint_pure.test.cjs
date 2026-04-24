"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");

const purePath = path.join(__dirname, "..", "..", "..", "static", "custom", "reconpoint_datatable_port_endpoint_pure.js");
if (!fs.existsSync(purePath)) {
  throw new Error("Expected pure helpers at " + purePath);
}

const {
  portDisplayParseStrictTcpPortString,
  reconpointNormalizeEndpointDefaultsTechnologiesFallback,
  reconpointIsEffectivelyEmptyHtml,
  reconpointValidEndpointDefaultRows,
  reconpointClassifyEndpointDefaultsByPortInput,
} = require(purePath);

test("portDisplayParseStrictTcpPortString accepts strict digit strings in range", () => {
  assert.equal(portDisplayParseStrictTcpPortString("443"), 443);
  assert.equal(portDisplayParseStrictTcpPortString("1"), 1);
  assert.equal(portDisplayParseStrictTcpPortString("65535"), 65535);
  assert.equal(portDisplayParseStrictTcpPortString(" 80 "), 80);
});

test("portDisplayParseStrictTcpPortString rejects prefixes and out-of-range", () => {
  assert.equal(portDisplayParseStrictTcpPortString("443xyz"), null);
  assert.equal(portDisplayParseStrictTcpPortString(""), null);
  assert.equal(portDisplayParseStrictTcpPortString("0"), null);
  assert.equal(portDisplayParseStrictTcpPortString("65536"), null);
  assert.equal(portDisplayParseStrictTcpPortString(null), null);
});

test("reconpointNormalizeEndpointDefaultsTechnologiesFallback", () => {
  assert.deepEqual(reconpointNormalizeEndpointDefaultsTechnologiesFallback([{ id: 1 }]), {
    technologies: [{ id: 1 }],
    content_type: "",
    webserver: "",
  });
  assert.deepEqual(reconpointNormalizeEndpointDefaultsTechnologiesFallback({ technologies: [], x: 1 }), {
    technologies: [],
    x: 1,
  });
  assert.equal(reconpointNormalizeEndpointDefaultsTechnologiesFallback(null), null);
});

test("reconpointIsEffectivelyEmptyHtml", () => {
  assert.equal(reconpointIsEffectivelyEmptyHtml(""), true);
  assert.equal(reconpointIsEffectivelyEmptyHtml("  \n\t "), true);
  assert.equal(reconpointIsEffectivelyEmptyHtml("<span>x</span>"), false);
});

test("reconpointValidEndpointDefaultRows filters non-objects", () => {
  assert.deepEqual(reconpointValidEndpointDefaultRows([1, null, { a: 1 }]), [{ a: 1 }]);
  assert.deepEqual(reconpointValidEndpointDefaultRows("x"), []);
});

test("reconpointClassifyEndpointDefaultsByPortInput branch coverage", () => {
  assert.equal(reconpointClassifyEndpointDefaultsByPortInput(undefined), "missing");
  assert.equal(reconpointClassifyEndpointDefaultsByPortInput(null), "missing");
  assert.equal(reconpointClassifyEndpointDefaultsByPortInput({}), "invalid_type");
  assert.equal(reconpointClassifyEndpointDefaultsByPortInput([]), "empty_valid_rows");
  assert.equal(reconpointClassifyEndpointDefaultsByPortInput([null, 1, "x"]), "empty_valid_rows");
  assert.equal(reconpointClassifyEndpointDefaultsByPortInput([{ port: 443 }]), "non_empty");
});
