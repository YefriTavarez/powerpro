(() => {
  var __create = Object.create;
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __getOwnPropSymbols = Object.getOwnPropertySymbols;
  var __getProtoOf = Object.getPrototypeOf;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __propIsEnum = Object.prototype.propertyIsEnumerable;
  var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
  var __spreadValues = (a, b) => {
    for (var prop in b || (b = {}))
      if (__hasOwnProp.call(b, prop))
        __defNormalProp(a, prop, b[prop]);
    if (__getOwnPropSymbols)
      for (var prop of __getOwnPropSymbols(b)) {
        if (__propIsEnum.call(b, prop))
          __defNormalProp(a, prop, b[prop]);
      }
    return a;
  };
  var __commonJS = (cb, mod) => function __require() {
    return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
    isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
    mod
  ));

  // ../powerpro/powerpro/public/js/controllers/functions.js
  var require_functions = __commonJS({
    "../powerpro/powerpro/public/js/controllers/functions.js"() {
      frappe.provide("power.utils");
      function round_to_nearest_multiple(number, multiple) {
        const value = flt(number, 3);
        return Math.round(value / multiple) * multiple;
      }
      function round_to_nearest_eighth(number) {
        return round_to_nearest_multiple(number, 1 / 8);
      }
      power.utils = {
        round_to_nearest_eighth
      };
    }
  });

  // ../powerpro/powerpro/public/js/vue/create_material_sku/index.js
  var require_create_material_sku = __commonJS({
    "../powerpro/powerpro/public/js/vue/create_material_sku/index.js"() {
      frappe.provide("power.ui");
      frappe.provide("power.utils");
      var { round_to_nearest_eighth } = power.utils;
      power.ui.CreateMaterialSKU = function(docname) {
        let theprompt;
        theprompt = frappe.prompt([
          {
            fieldname: "material_format",
            fieldtype: "Select",
            label: __("Material Format"),
            reqd: 1,
            default: "Roll",
            options: [
              "Roll",
              "Sheet"
            ],
            change(event) {
              theprompt.set_df_property("roll_width", "reqd", event.target.value === "Roll");
              theprompt.set_df_property("roll_width", "hidden", event.target.value === "Sheet");
              theprompt.set_df_property("sheet_width", "reqd", event.target.value === "Sheet");
              theprompt.set_df_property("sheet_width", "hidden", event.target.value === "Roll");
              theprompt.set_df_property("sheet_height", "reqd", event.target.value === "Sheet");
              theprompt.set_df_property("sheet_height", "hidden", event.target.value === "Roll");
            }
          },
          { fieldtype: "Column Break" },
          {
            fieldname: "roll_width",
            fieldtype: "Float",
            label: __("Roll Width"),
            reqd: 1,
            precision: 3,
            async change(event) {
              const { target } = event;
              await frappe.timeout(0.1);
              const value = round_to_nearest_eighth(target.value);
              if (target.value !== value) {
                target.value = value;
              }
            }
          },
          {
            fieldname: "sheet_width",
            fieldtype: "Float",
            label: __("Sheet Width"),
            hidden: 1,
            precision: 3,
            async change(event) {
              const { target } = event;
              await frappe.timeout(0.1);
              const value = round_to_nearest_eighth(target.value);
              if (target.value !== value) {
                target.value = value;
              }
            }
          },
          {
            fieldname: "sheet_height",
            fieldtype: "Float",
            label: __("Sheet Height"),
            hidden: 1,
            precision: 3,
            async change(event) {
              const { target } = event;
              await frappe.timeout(0.1);
              const value = round_to_nearest_eighth(target.value);
              if (target.value !== value) {
                target.value = value;
              }
            }
          }
        ], function(values) {
          frappe.call("powerpro.manufacturing_pro.doctype.raw_material.client.create_material_sku", __spreadValues({
            material_id: docname
          }, values)).then(function(response) {
            const { message } = response;
            if (message) {
              frappe.confirm(`
					Here is the SKU <strong>${message}</strong>
					<button class="btn btn-info" onclick="frappe.utils.copy_to_clipboard('${message}')">Copy to Clipboard</button>
					<br>Do you want me to take you there?
				`, () => {
                frappe.set_route("Form", "Item", message);
              }, () => {
                frappe.show_alert({
                  message: __("Alright... let's be productive, then!"),
                  indicator: "green"
                });
              });
              frappe.show_alert({
                message,
                indicator: "green"
              });
            } else {
              frappe.show_alert({
                message: __("SKU not created!"),
                indicator: "red"
              });
              frappe.confirm(
                __("Would you like to try again?"),
                () => theprompt.show(),
                () => frappe.show_alert(__("Okay!"))
              );
            }
          }, function(exec) {
            frappe.show_alert({
              message: __("SKU not created!"),
              indicator: "red"
            });
            frappe.confirm(
              __("Would you like to try again?"),
              () => theprompt.show(),
              () => frappe.show_alert(__("Okay!"))
            );
          });
        }, "Create a new SKU", "Please, do!");
      };
    }
  });

  // ../powerpro/powerpro/public/js/app.bundle.js
  var functions = __toESM(require_functions());
  var create_material_sku = __toESM(require_create_material_sku());
})();
//# sourceMappingURL=app.bundle.4F377NYD.js.map
