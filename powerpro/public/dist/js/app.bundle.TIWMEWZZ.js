frappe.dom.set_style("/* sfc-style:/home/frappe/yefri-bench/apps/frappe/frappe/public/js/frappe/file_uploader/ProgressRing.vue?type=style&index=0 */\ncircle[data-v-e4881e80] {\n  transition: stroke-dashoffset 0.35s;\n  transform: rotate(-90deg);\n  transform-origin: 50% 50%;\n}\n\n/* sfc-style:/home/frappe/yefri-bench/apps/frappe/frappe/public/js/frappe/file_uploader/FilePreview.vue?type=style&index=0 */\n.file-preview[data-v-d6847533] {\n  display: flex;\n  align-items: center;\n  padding: 0.75rem;\n  border: 1px solid transparent;\n}\n.file-preview + .file-preview[data-v-d6847533] {\n  border-top-color: var(--border-color);\n}\n.file-preview[data-v-d6847533]:hover {\n  background-color: var(--bg-color);\n  border-color: var(--dark-border-color);\n  border-radius: var(--border-radius);\n}\n.file-preview:hover + .file-preview[data-v-d6847533] {\n  border-top-color: transparent;\n}\n.file-icon[data-v-d6847533] {\n  border-radius: var(--border-radius);\n  width: 2.625rem;\n  height: 2.625rem;\n  overflow: hidden;\n  margin-right: var(--margin-md);\n  flex-shrink: 0;\n}\n.file-icon img[data-v-d6847533] {\n  width: 100%;\n  height: 100%;\n  object-fit: cover;\n}\n.file-icon .fallback[data-v-d6847533] {\n  width: 100%;\n  height: 100%;\n  display: flex;\n  align-items: center;\n  justify-content: center;\n  border: 1px solid var(--border-color);\n  border-radius: var(--border-radius);\n}\n.file-name[data-v-d6847533] {\n  font-size: var(--text-base);\n  font-weight: var(--text-bold);\n  color: var(--text-color);\n  display: -webkit-box;\n  -webkit-line-clamp: 1;\n  -webkit-box-orient: vertical;\n  overflow: hidden;\n}\n.file-size[data-v-d6847533] {\n  font-size: var(--text-sm);\n  color: var(--text-light);\n}\n.file-actions[data-v-d6847533] {\n  width: 3rem;\n  flex-shrink: 0;\n  margin-left: auto;\n  text-align: center;\n}\n.file-actions .btn[data-v-d6847533] {\n  padding: var(--padding-xs);\n  box-shadow: none;\n}\n.file-action-buttons[data-v-d6847533] {\n  display: flex;\n  justify-content: flex-end;\n}\n.muted[data-v-d6847533] {\n  opacity: 0.5;\n  transition: 0.3s;\n}\n.muted[data-v-d6847533]:hover {\n  opacity: 1;\n}\n.frappe-checkbox[data-v-d6847533] {\n  font-size: var(--text-sm);\n  color: var(--text-light);\n  display: flex;\n  align-items: center;\n  padding-top: 0.25rem;\n}\n.config-area[data-v-d6847533] {\n  gap: 0.5rem;\n}\n.file-error[data-v-d6847533] {\n  font-size: var(--text-sm);\n  font-weight: var(--text-bold);\n}\n\n/* sfc-style:/home/frappe/yefri-bench/apps/frappe/frappe/public/js/frappe/file_uploader/TreeNode.vue?type=style&index=0 */\n.btn-load-more[data-v-877e6dee] {\n  margin-left: 1.6rem;\n  margin-top: 0.5rem;\n}\n.popover[data-v-877e6dee] {\n  padding: 10px;\n}\n\n/* sfc-style:/home/frappe/yefri-bench/apps/frappe/frappe/public/js/frappe/file_uploader/FileBrowser.vue?type=style&index=0 */\n.file-browser-list[data-v-1d966cc2] {\n  height: 300px;\n  overflow: hidden;\n  margin-top: 10px;\n}\n.file-filter[data-v-1d966cc2] {\n  padding: 3px;\n}\n.tree[data-v-1d966cc2] {\n  overflow: auto;\n  height: 100%;\n  padding-left: 0;\n  padding-right: 0;\n  padding-bottom: 4rem;\n}\n\n/* sfc-style:/home/frappe/yefri-bench/apps/frappe/frappe/public/js/frappe/file_uploader/WebLink.vue?type=style&index=0 */\n.file-web-link .input-group[data-v-55466dd8] {\n  margin-top: 10px;\n}\n\n/* node_modules/cropperjs/dist/cropper.min.css */\n.cropper-container {\n  direction: ltr;\n  font-size: 0;\n  line-height: 0;\n  position: relative;\n  -ms-touch-action: none;\n  touch-action: none;\n  -webkit-user-select: none;\n  -moz-user-select: none;\n  -ms-user-select: none;\n  user-select: none;\n}\n.cropper-container img {\n  backface-visibility: hidden;\n  display: block;\n  height: 100%;\n  image-orientation: 0deg;\n  max-height: none !important;\n  max-width: none !important;\n  min-height: 0 !important;\n  min-width: 0 !important;\n  width: 100%;\n}\n.cropper-canvas,\n.cropper-crop-box,\n.cropper-drag-box,\n.cropper-modal,\n.cropper-wrap-box {\n  bottom: 0;\n  left: 0;\n  position: absolute;\n  right: 0;\n  top: 0;\n}\n.cropper-canvas,\n.cropper-wrap-box {\n  overflow: hidden;\n}\n.cropper-drag-box {\n  background-color: #fff;\n  opacity: 0;\n}\n.cropper-modal {\n  background-color: #000;\n  opacity: .5;\n}\n.cropper-view-box {\n  display: block;\n  height: 100%;\n  outline: 1px solid #39f;\n  outline-color: rgba(51, 153, 255, .75);\n  overflow: hidden;\n  width: 100%;\n}\n.cropper-dashed {\n  border: 0 dashed #eee;\n  display: block;\n  opacity: .5;\n  position: absolute;\n}\n.cropper-dashed.dashed-h {\n  border-bottom-width: 1px;\n  border-top-width: 1px;\n  height: 33.33333%;\n  left: 0;\n  top: 33.33333%;\n  width: 100%;\n}\n.cropper-dashed.dashed-v {\n  border-left-width: 1px;\n  border-right-width: 1px;\n  height: 100%;\n  left: 33.33333%;\n  top: 0;\n  width: 33.33333%;\n}\n.cropper-center {\n  display: block;\n  height: 0;\n  left: 50%;\n  opacity: .75;\n  position: absolute;\n  top: 50%;\n  width: 0;\n}\n.cropper-center:after,\n.cropper-center:before {\n  background-color: #eee;\n  content: \" \";\n  display: block;\n  position: absolute;\n}\n.cropper-center:before {\n  height: 1px;\n  left: -3px;\n  top: 0;\n  width: 7px;\n}\n.cropper-center:after {\n  height: 7px;\n  left: 0;\n  top: -3px;\n  width: 1px;\n}\n.cropper-face,\n.cropper-line,\n.cropper-point {\n  display: block;\n  height: 100%;\n  opacity: .1;\n  position: absolute;\n  width: 100%;\n}\n.cropper-face {\n  background-color: #fff;\n  left: 0;\n  top: 0;\n}\n.cropper-line {\n  background-color: #39f;\n}\n.cropper-line.line-e {\n  cursor: ew-resize;\n  right: -3px;\n  top: 0;\n  width: 5px;\n}\n.cropper-line.line-n {\n  cursor: ns-resize;\n  height: 5px;\n  left: 0;\n  top: -3px;\n}\n.cropper-line.line-w {\n  cursor: ew-resize;\n  left: -3px;\n  top: 0;\n  width: 5px;\n}\n.cropper-line.line-s {\n  bottom: -3px;\n  cursor: ns-resize;\n  height: 5px;\n  left: 0;\n}\n.cropper-point {\n  background-color: #39f;\n  height: 5px;\n  opacity: .75;\n  width: 5px;\n}\n.cropper-point.point-e {\n  cursor: ew-resize;\n  margin-top: -3px;\n  right: -3px;\n  top: 50%;\n}\n.cropper-point.point-n {\n  cursor: ns-resize;\n  left: 50%;\n  margin-left: -3px;\n  top: -3px;\n}\n.cropper-point.point-w {\n  cursor: ew-resize;\n  left: -3px;\n  margin-top: -3px;\n  top: 50%;\n}\n.cropper-point.point-s {\n  bottom: -3px;\n  cursor: s-resize;\n  left: 50%;\n  margin-left: -3px;\n}\n.cropper-point.point-ne {\n  cursor: nesw-resize;\n  right: -3px;\n  top: -3px;\n}\n.cropper-point.point-nw {\n  cursor: nwse-resize;\n  left: -3px;\n  top: -3px;\n}\n.cropper-point.point-sw {\n  bottom: -3px;\n  cursor: nesw-resize;\n  left: -3px;\n}\n.cropper-point.point-se {\n  bottom: -3px;\n  cursor: nwse-resize;\n  height: 20px;\n  opacity: 1;\n  right: -3px;\n  width: 20px;\n}\n@media (min-width:768px) {\n  .cropper-point.point-se {\n    height: 15px;\n    width: 15px;\n  }\n}\n@media (min-width:992px) {\n  .cropper-point.point-se {\n    height: 10px;\n    width: 10px;\n  }\n}\n@media (min-width:1200px) {\n  .cropper-point.point-se {\n    height: 5px;\n    opacity: .75;\n    width: 5px;\n  }\n}\n.cropper-point.point-se:before {\n  background-color: #39f;\n  bottom: -50%;\n  content: \" \";\n  display: block;\n  height: 200%;\n  opacity: 0;\n  position: absolute;\n  right: -50%;\n  width: 200%;\n}\n.cropper-invisible {\n  opacity: 0;\n}\n.cropper-bg {\n  background-image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQAQMAAAAlPW0iAAAAA3NCSVQICAjb4U/gAAAABlBMVEXMzMz////TjRV2AAAACXBIWXMAAArrAAAK6wGCiw1aAAAAHHRFWHRTb2Z0d2FyZQBBZG9iZSBGaXJld29ya3MgQ1M26LyyjAAAABFJREFUCJlj+M/AgBVhF/0PAH6/D/HkDxOGAAAAAElFTkSuQmCC);\n}\n.cropper-hide {\n  display: block;\n  height: 0;\n  position: absolute;\n  width: 0;\n}\n.cropper-hidden {\n  display: none !important;\n}\n.cropper-move {\n  cursor: move;\n}\n.cropper-crop {\n  cursor: crosshair;\n}\n.cropper-disabled .cropper-drag-box,\n.cropper-disabled .cropper-face,\n.cropper-disabled .cropper-line,\n.cropper-disabled .cropper-point {\n  cursor: not-allowed;\n}\n\n/* sfc-style:/home/frappe/yefri-bench/apps/frappe/frappe/public/js/frappe/file_uploader/ImageCropper.vue?type=style&index=0 */\nimg[data-v-21184c3b] {\n  display: block;\n  max-width: 100%;\n  max-height: 600px;\n}\n.image-cropper-actions[data-v-21184c3b] {\n  display: flex;\n  align-items: center;\n  justify-content: space-between;\n  margin-top: var(--margin-md);\n}\n\n/* sfc-style:/home/frappe/yefri-bench/apps/powerpro/powerpro/public/js/frappe/FileUploader.vue?type=style&index=0 */\n.file-upload-area[data-v-b962aefe] {\n  min-height: 16rem;\n  display: flex;\n  align-items: center;\n  justify-content: center;\n  border: 1px dashed var(--dark-border-color);\n  border-radius: var(--border-radius);\n  cursor: pointer;\n  background-color: var(--bg-color);\n}\n.btn-file-upload[data-v-b962aefe] {\n  background-color: transparent;\n  border: none;\n  box-shadow: none;\n  font-size: var(--text-xs);\n}\n/*!\n * Cropper.js v1.6.1\n * https://fengyuanchen.github.io/cropperjs\n *\n * Copyright 2015-present Chen Fengyuan\n * Released under the MIT license\n *\n * Date: 2023-09-17T03:44:17.565Z\n */\n/*# sourceMappingURL=app.bundle.PHO75LIU.css.map */\n");
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
      function round_to_nearest_multiple(value, multiple) {
        return Math.ceil(value / multiple) * multiple;
      }
      function round_to_nearest_multiple_without_roundup(value, multiple) {
        return Math.round(value / multiple) * multiple;
      }
      function round_to_nearest_eighth(number, roundup) {
        if (roundup) {
          return round_to_nearest_multiple(number, 1 / 8);
        }
        return round_to_nearest_multiple_without_roundup(number, 1 / 8);
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
        let dialog;
        let item_group_details;
        let doc2;
        const url = "/api/method/powerpro.controllers.assets.item_group.get_all_item_groups";
        frappe.dom.freeze(__("Loading..."));
        fetch(url).then((response) => response.json()).then(({ message }) => {
          item_group_details = message;
        });
        fetch(`/api/resource/Raw Material/${docname}`).then((response) => response.json()).then(({ data }) => {
          doc2 = data;
          const description_field = dialog.get_field("material_description");
          description_field.$wrapper.html(`
				<p class="text-muted">Material</p>
				<h3>${doc2.description}</h3>
			`);
          _render_dialog(doc2);
        }).finally(() => {
          frappe.dom.unfreeze();
        });
        function _render_dialog(form) {
          var _a, _b, _c, _d;
          dialog = new frappe.ui.Dialog({
            title: __("Create a new SKU"),
            size: "extra-large",
            fields: [
              {
                fieldtype: "HTML",
                fieldname: "material_description",
                options: `Loading...`
              },
              {
                fieldtype: "Section Break",
                label: __("Material Specification")
              },
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
                  dialog.set_df_property("roll_width", "reqd", event.target.value === "Roll");
                  dialog.set_df_property("roll_width", "hidden", event.target.value === "Sheet");
                  dialog.set_df_property("sheet_width", "reqd", event.target.value === "Sheet");
                  dialog.set_df_property("sheet_width", "hidden", event.target.value === "Roll");
                  dialog.set_df_property("sheet_height", "reqd", event.target.value === "Sheet");
                  dialog.set_df_property("sheet_height", "hidden", event.target.value === "Roll");
                  dialog.set_df_property("standard_sheet_size", "hidden", event.target.value === "Roll");
                }
              },
              {
                fieldname: "standard_sheet_size",
                fieldtype: "Select",
                label: __("Standard Sheet Size"),
                reqd: 1,
                default: "",
                options: [
                  "",
                  "Standard",
                  "Derivado"
                ],
                change(event) {
                  const gsm = dialog.get_value("gsm");
                  const material_format = dialog.get_value("material_format");
                  const standard_sheet_size = dialog.get_value("standard_sheet_size");
                  const hidden = material_format !== "Sheet" || standard_sheet_size !== "Derivado" || !gsm;
                  dialog.set_df_property("standard_sheets_section", "hidden", hidden);
                  dialog.set_df_property("standard_sheets", "hidden", hidden);
                }
              },
              { fieldtype: "Column Break" },
              {
                fieldname: "roll_width",
                fieldtype: "Float",
                label: `${__("Roll Width")} (in)`,
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
                label: `${__("Sheet Width")} (in)`,
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
                label: `${__("Sheet Height")} (in)`,
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
                fieldtype: "Section Break",
                label: __("Weight")
              },
              {
                fieldname: "gsm",
                fieldtype: "Int",
                non_negative: 1,
                reqd: 1,
                label: __("GSM"),
                async change(event) {
                  const { target } = event;
                  await frappe.timeout(0.1);
                  if (!target.value) {
                    target.value = 0;
                  }
                  if (target.value < 0) {
                    target.value = 0;
                    frappe.show_alert({
                      message: __("GSM cannot be negative!"),
                      indicator: "red"
                    });
                  }
                  const gsm = dialog.get_value("gsm");
                  const material_format = dialog.get_value("material_format");
                  const standard_sheet_size = dialog.get_value("standard_sheet_size");
                  const hidden = material_format !== "Sheet" || standard_sheet_size !== "Derivado" || !gsm;
                  dialog.set_df_property("standard_sheets_section", "hidden", hidden);
                  dialog.set_df_property("standard_sheets", "hidden", hidden);
                }
              },
              { fieldtype: "Section Break", fieldname: "standard_sheets_section" },
              {
                fieldname: "standard_sheets",
                fieldtype: "Table",
                label: __("Standard Sheets"),
                reqd: 1,
                cannot_add_rows: 0,
                in_place_edit: true,
                data: [{
                  item: "",
                  "description": ""
                }],
                get_data: () => {
                  return [];
                },
                fields: [
                  {
                    fieldname: "item",
                    fieldtype: "Link",
                    options: "Item",
                    label: __("Item"),
                    in_list_view: 1,
                    reqd: 1,
                    get_query(doc3) {
                      const gsm = dialog.get_value("gsm");
                      return {
                        filters: {
                          "reference_name": docname,
                          "is_standard_sheet_size": 1,
                          "raw_material_type": "Sheet",
                          "gsm": gsm,
                          "name": [
                            "not in",
                            dialog.get_value("standard_sheets").filter((row) => row.name !== doc3.name).map((row) => row.item)
                          ]
                        }
                      };
                    },
                    onchange() {
                      const { grid_row } = this;
                      const { description } = grid_row.on_grid_fields_dict;
                      const { value } = this;
                      if (value) {
                        frappe.db.get_value("Item", value, ["description"]).then(({ message }) => {
                          if (message.description) {
                            description.set_value(message.description);
                          }
                        });
                      }
                    }
                  },
                  {
                    fieldname: "description",
                    fieldtype: "Small Text",
                    label: __("Description"),
                    in_list_view: 1
                  }
                ]
              },
              {
                fieldtype: "Section Break",
                label: __("Item Group")
              },
              {
                fieldname: "item_group_1",
                fieldtype: "Link",
                label: __("Item Group 1"),
                options: "Item Group",
                default: form.item_group_1 || ((_b = (_a = frappe.boot) == null ? void 0 : _a.powerpro_settings) == null ? void 0 : _b.root_item_group_for_raw_materials),
                read_only: Boolean((_d = (_c = frappe.boot) == null ? void 0 : _c.powerpro_settings) == null ? void 0 : _d.root_item_group_for_raw_materials),
                reqd: 1,
                change(event) {
                }
              },
              {
                fieldname: "item_group_2",
                fieldtype: "Link",
                label: __("Item Group 2"),
                options: "Item Group",
                default: form.item_group_2,
                reqd: 1,
                get_query() {
                  return {
                    filters: {
                      parent_item_group: dialog.get_value("item_group_1")
                    }
                  };
                },
                change(event) {
                  const { value } = this;
                  if (value) {
                    const has_children = item_group_details.find((item_group) => item_group.parent_item_group === value);
                    dialog.set_df_property("item_group_3", "hidden", !has_children);
                    dialog.set_df_property("item_group_3", "reqd", has_children);
                  } else {
                    dialog.set_df_property("item_group_5", "hidden", 1);
                    dialog.set_df_property("item_group_3", "reqd", 0);
                  }
                  dialog.set_value("item_group_3", null);
                }
              },
              {
                fieldname: "item_group_3",
                fieldtype: "Link",
                label: __("Item Group 3"),
                options: "Item Group",
                default: form.item_group_3,
                hidden: 1,
                get_query() {
                  return {
                    filters: {
                      parent_item_group: dialog.get_value("item_group_2")
                    }
                  };
                },
                change(event) {
                  const { value } = this;
                  if (value) {
                    const has_children = item_group_details.find((item_group) => item_group.parent_item_group === value);
                    dialog.set_df_property("item_group_4", "hidden", !has_children);
                    dialog.set_df_property("item_group_4", "reqd", has_children);
                  } else {
                    dialog.set_df_property("item_group_4", "hidden", 1);
                    dialog.set_df_property("item_group_4", "reqd", 0);
                  }
                  dialog.set_value("item_group_4", null);
                }
              },
              {
                fieldname: "item_group_4",
                fieldtype: "Link",
                label: __("Item Group 4"),
                default: form.item_group_4,
                options: "Item Group",
                hidden: 1,
                get_query() {
                  return {
                    filters: {
                      parent_item_group: dialog.get_value("item_group_3")
                    }
                  };
                },
                change(event) {
                  const { value } = this;
                  if (value) {
                    const has_children = item_group_details.find((item_group) => item_group.parent_item_group === value);
                    dialog.set_df_property("item_group_5", "hidden", !has_children);
                    dialog.set_df_property("item_group_5", "reqd", has_children);
                  } else {
                    dialog.set_df_property("item_group_5", "hidden", 1);
                    dialog.set_df_property("item_group_5", "reqd", 0);
                  }
                  dialog.set_value("item_group_5", null);
                }
              },
              {
                fieldname: "item_group_5",
                fieldtype: "Link",
                label: __("Item Group 5"),
                options: "Item Group",
                default: form.item_group_5,
                hidden: 1,
                get_query() {
                  return {
                    filters: {
                      parent_item_group: dialog.get_value("item_group_4")
                    }
                  };
                },
                change(event) {
                }
              }
            ],
            primary_action_label: __("Please, do!"),
            primary_action(values) {
              frappe.call("powerpro.manufacturing_pro.doctype.raw_material.client.create_material_sku", __spreadValues({
                material_id: docname
              }, values)).then(function(response) {
                const { message } = response;
                if (message) {
                  dialog.hide();
                  frappe.confirm(`
							${__("Here is the SKU")} <strong>${message}</strong>
							<button class="btn btn-info" onclick="frappe.utils.copy_to_clipboard('${message}')">
								${__("Copy to Clipboard")}
							</button>
							<br>${__("Do you want me to take you there?")}
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
                    () => dialog.show(),
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
                  () => dialog.show(),
                  () => frappe.show_alert(__("Okay!"))
                );
              });
            }
          });
          dialog.set_df_property("standard_sheet_size", "hidden", 1);
          dialog.set_df_property("standard_sheets_section", "hidden", 1);
          dialog.set_df_property("standard_sheets", "hidden", 1);
          dialog.show();
        }
      };
    }
  });

  // node_modules/cropperjs/dist/cropper.js
  var require_cropper = __commonJS({
    "node_modules/cropperjs/dist/cropper.js"(exports, module) {
      (function(global2, factory) {
        typeof exports === "object" && typeof module !== "undefined" ? module.exports = factory() : typeof define === "function" && define.amd ? define(factory) : (global2 = typeof globalThis !== "undefined" ? globalThis : global2 || self, global2.Cropper = factory());
      })(exports, function() {
        "use strict";
        function ownKeys(e, r) {
          var t = Object.keys(e);
          if (Object.getOwnPropertySymbols) {
            var o = Object.getOwnPropertySymbols(e);
            r && (o = o.filter(function(r2) {
              return Object.getOwnPropertyDescriptor(e, r2).enumerable;
            })), t.push.apply(t, o);
          }
          return t;
        }
        function _objectSpread2(e) {
          for (var r = 1; r < arguments.length; r++) {
            var t = null != arguments[r] ? arguments[r] : {};
            r % 2 ? ownKeys(Object(t), true).forEach(function(r2) {
              _defineProperty(e, r2, t[r2]);
            }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function(r2) {
              Object.defineProperty(e, r2, Object.getOwnPropertyDescriptor(t, r2));
            });
          }
          return e;
        }
        function _typeof(o) {
          "@babel/helpers - typeof";
          return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function(o2) {
            return typeof o2;
          } : function(o2) {
            return o2 && "function" == typeof Symbol && o2.constructor === Symbol && o2 !== Symbol.prototype ? "symbol" : typeof o2;
          }, _typeof(o);
        }
        function _classCallCheck(instance, Constructor) {
          if (!(instance instanceof Constructor)) {
            throw new TypeError("Cannot call a class as a function");
          }
        }
        function _defineProperties(target, props) {
          for (var i = 0; i < props.length; i++) {
            var descriptor = props[i];
            descriptor.enumerable = descriptor.enumerable || false;
            descriptor.configurable = true;
            if ("value" in descriptor)
              descriptor.writable = true;
            Object.defineProperty(target, _toPropertyKey(descriptor.key), descriptor);
          }
        }
        function _createClass(Constructor, protoProps, staticProps) {
          if (protoProps)
            _defineProperties(Constructor.prototype, protoProps);
          if (staticProps)
            _defineProperties(Constructor, staticProps);
          Object.defineProperty(Constructor, "prototype", {
            writable: false
          });
          return Constructor;
        }
        function _defineProperty(obj, key, value) {
          key = _toPropertyKey(key);
          if (key in obj) {
            Object.defineProperty(obj, key, {
              value,
              enumerable: true,
              configurable: true,
              writable: true
            });
          } else {
            obj[key] = value;
          }
          return obj;
        }
        function _toConsumableArray(arr) {
          return _arrayWithoutHoles(arr) || _iterableToArray(arr) || _unsupportedIterableToArray(arr) || _nonIterableSpread();
        }
        function _arrayWithoutHoles(arr) {
          if (Array.isArray(arr))
            return _arrayLikeToArray(arr);
        }
        function _iterableToArray(iter) {
          if (typeof Symbol !== "undefined" && iter[Symbol.iterator] != null || iter["@@iterator"] != null)
            return Array.from(iter);
        }
        function _unsupportedIterableToArray(o, minLen) {
          if (!o)
            return;
          if (typeof o === "string")
            return _arrayLikeToArray(o, minLen);
          var n = Object.prototype.toString.call(o).slice(8, -1);
          if (n === "Object" && o.constructor)
            n = o.constructor.name;
          if (n === "Map" || n === "Set")
            return Array.from(o);
          if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n))
            return _arrayLikeToArray(o, minLen);
        }
        function _arrayLikeToArray(arr, len) {
          if (len == null || len > arr.length)
            len = arr.length;
          for (var i = 0, arr2 = new Array(len); i < len; i++)
            arr2[i] = arr[i];
          return arr2;
        }
        function _nonIterableSpread() {
          throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
        }
        function _toPrimitive(input, hint) {
          if (typeof input !== "object" || input === null)
            return input;
          var prim = input[Symbol.toPrimitive];
          if (prim !== void 0) {
            var res = prim.call(input, hint || "default");
            if (typeof res !== "object")
              return res;
            throw new TypeError("@@toPrimitive must return a primitive value.");
          }
          return (hint === "string" ? String : Number)(input);
        }
        function _toPropertyKey(arg) {
          var key = _toPrimitive(arg, "string");
          return typeof key === "symbol" ? key : String(key);
        }
        var IS_BROWSER = typeof window !== "undefined" && typeof window.document !== "undefined";
        var WINDOW = IS_BROWSER ? window : {};
        var IS_TOUCH_DEVICE = IS_BROWSER && WINDOW.document.documentElement ? "ontouchstart" in WINDOW.document.documentElement : false;
        var HAS_POINTER_EVENT = IS_BROWSER ? "PointerEvent" in WINDOW : false;
        var NAMESPACE = "cropper";
        var ACTION_ALL = "all";
        var ACTION_CROP = "crop";
        var ACTION_MOVE = "move";
        var ACTION_ZOOM = "zoom";
        var ACTION_EAST = "e";
        var ACTION_WEST = "w";
        var ACTION_SOUTH = "s";
        var ACTION_NORTH = "n";
        var ACTION_NORTH_EAST = "ne";
        var ACTION_NORTH_WEST = "nw";
        var ACTION_SOUTH_EAST = "se";
        var ACTION_SOUTH_WEST = "sw";
        var CLASS_CROP = "".concat(NAMESPACE, "-crop");
        var CLASS_DISABLED = "".concat(NAMESPACE, "-disabled");
        var CLASS_HIDDEN = "".concat(NAMESPACE, "-hidden");
        var CLASS_HIDE = "".concat(NAMESPACE, "-hide");
        var CLASS_INVISIBLE = "".concat(NAMESPACE, "-invisible");
        var CLASS_MODAL = "".concat(NAMESPACE, "-modal");
        var CLASS_MOVE = "".concat(NAMESPACE, "-move");
        var DATA_ACTION = "".concat(NAMESPACE, "Action");
        var DATA_PREVIEW = "".concat(NAMESPACE, "Preview");
        var DRAG_MODE_CROP = "crop";
        var DRAG_MODE_MOVE = "move";
        var DRAG_MODE_NONE = "none";
        var EVENT_CROP = "crop";
        var EVENT_CROP_END = "cropend";
        var EVENT_CROP_MOVE = "cropmove";
        var EVENT_CROP_START = "cropstart";
        var EVENT_DBLCLICK = "dblclick";
        var EVENT_TOUCH_START = IS_TOUCH_DEVICE ? "touchstart" : "mousedown";
        var EVENT_TOUCH_MOVE = IS_TOUCH_DEVICE ? "touchmove" : "mousemove";
        var EVENT_TOUCH_END = IS_TOUCH_DEVICE ? "touchend touchcancel" : "mouseup";
        var EVENT_POINTER_DOWN = HAS_POINTER_EVENT ? "pointerdown" : EVENT_TOUCH_START;
        var EVENT_POINTER_MOVE = HAS_POINTER_EVENT ? "pointermove" : EVENT_TOUCH_MOVE;
        var EVENT_POINTER_UP = HAS_POINTER_EVENT ? "pointerup pointercancel" : EVENT_TOUCH_END;
        var EVENT_READY = "ready";
        var EVENT_RESIZE = "resize";
        var EVENT_WHEEL = "wheel";
        var EVENT_ZOOM = "zoom";
        var MIME_TYPE_JPEG = "image/jpeg";
        var REGEXP_ACTIONS = /^e|w|s|n|se|sw|ne|nw|all|crop|move|zoom$/;
        var REGEXP_DATA_URL = /^data:/;
        var REGEXP_DATA_URL_JPEG = /^data:image\/jpeg;base64,/;
        var REGEXP_TAG_NAME = /^img|canvas$/i;
        var MIN_CONTAINER_WIDTH = 200;
        var MIN_CONTAINER_HEIGHT = 100;
        var DEFAULTS = {
          viewMode: 0,
          dragMode: DRAG_MODE_CROP,
          initialAspectRatio: NaN,
          aspectRatio: NaN,
          data: null,
          preview: "",
          responsive: true,
          restore: true,
          checkCrossOrigin: true,
          checkOrientation: true,
          modal: true,
          guides: true,
          center: true,
          highlight: true,
          background: true,
          autoCrop: true,
          autoCropArea: 0.8,
          movable: true,
          rotatable: true,
          scalable: true,
          zoomable: true,
          zoomOnTouch: true,
          zoomOnWheel: true,
          wheelZoomRatio: 0.1,
          cropBoxMovable: true,
          cropBoxResizable: true,
          toggleDragModeOnDblclick: true,
          minCanvasWidth: 0,
          minCanvasHeight: 0,
          minCropBoxWidth: 0,
          minCropBoxHeight: 0,
          minContainerWidth: MIN_CONTAINER_WIDTH,
          minContainerHeight: MIN_CONTAINER_HEIGHT,
          ready: null,
          cropstart: null,
          cropmove: null,
          cropend: null,
          crop: null,
          zoom: null
        };
        var TEMPLATE = '<div class="cropper-container" touch-action="none"><div class="cropper-wrap-box"><div class="cropper-canvas"></div></div><div class="cropper-drag-box"></div><div class="cropper-crop-box"><span class="cropper-view-box"></span><span class="cropper-dashed dashed-h"></span><span class="cropper-dashed dashed-v"></span><span class="cropper-center"></span><span class="cropper-face"></span><span class="cropper-line line-e" data-cropper-action="e"></span><span class="cropper-line line-n" data-cropper-action="n"></span><span class="cropper-line line-w" data-cropper-action="w"></span><span class="cropper-line line-s" data-cropper-action="s"></span><span class="cropper-point point-e" data-cropper-action="e"></span><span class="cropper-point point-n" data-cropper-action="n"></span><span class="cropper-point point-w" data-cropper-action="w"></span><span class="cropper-point point-s" data-cropper-action="s"></span><span class="cropper-point point-ne" data-cropper-action="ne"></span><span class="cropper-point point-nw" data-cropper-action="nw"></span><span class="cropper-point point-sw" data-cropper-action="sw"></span><span class="cropper-point point-se" data-cropper-action="se"></span></div></div>';
        var isNaN2 = Number.isNaN || WINDOW.isNaN;
        function isNumber(value) {
          return typeof value === "number" && !isNaN2(value);
        }
        var isPositiveNumber = function isPositiveNumber2(value) {
          return value > 0 && value < Infinity;
        };
        function isUndefined(value) {
          return typeof value === "undefined";
        }
        function isObject3(value) {
          return _typeof(value) === "object" && value !== null;
        }
        var hasOwnProperty5 = Object.prototype.hasOwnProperty;
        function isPlainObject3(value) {
          if (!isObject3(value)) {
            return false;
          }
          try {
            var _constructor = value.constructor;
            var prototype = _constructor.prototype;
            return _constructor && prototype && hasOwnProperty5.call(prototype, "isPrototypeOf");
          } catch (error) {
            return false;
          }
        }
        function isFunction3(value) {
          return typeof value === "function";
        }
        var slice = Array.prototype.slice;
        function toArray(value) {
          return Array.from ? Array.from(value) : slice.call(value);
        }
        function forEach(data, callback) {
          if (data && isFunction3(callback)) {
            if (Array.isArray(data) || isNumber(data.length)) {
              toArray(data).forEach(function(value, key) {
                callback.call(data, value, key, data);
              });
            } else if (isObject3(data)) {
              Object.keys(data).forEach(function(key) {
                callback.call(data, data[key], key, data);
              });
            }
          }
          return data;
        }
        var assign = Object.assign || function assign2(target) {
          for (var _len = arguments.length, args = new Array(_len > 1 ? _len - 1 : 0), _key = 1; _key < _len; _key++) {
            args[_key - 1] = arguments[_key];
          }
          if (isObject3(target) && args.length > 0) {
            args.forEach(function(arg) {
              if (isObject3(arg)) {
                Object.keys(arg).forEach(function(key) {
                  target[key] = arg[key];
                });
              }
            });
          }
          return target;
        };
        var REGEXP_DECIMALS = /\.\d*(?:0|9){12}\d*$/;
        function normalizeDecimalNumber(value) {
          var times = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : 1e11;
          return REGEXP_DECIMALS.test(value) ? Math.round(value * times) / times : value;
        }
        var REGEXP_SUFFIX = /^width|height|left|top|marginLeft|marginTop$/;
        function setStyle2(element, styles) {
          var style = element.style;
          forEach(styles, function(value, property) {
            if (REGEXP_SUFFIX.test(property) && isNumber(value)) {
              value = "".concat(value, "px");
            }
            style[property] = value;
          });
        }
        function hasClass(element, value) {
          return element.classList ? element.classList.contains(value) : element.className.indexOf(value) > -1;
        }
        function addClass(element, value) {
          if (!value) {
            return;
          }
          if (isNumber(element.length)) {
            forEach(element, function(elem) {
              addClass(elem, value);
            });
            return;
          }
          if (element.classList) {
            element.classList.add(value);
            return;
          }
          var className = element.className.trim();
          if (!className) {
            element.className = value;
          } else if (className.indexOf(value) < 0) {
            element.className = "".concat(className, " ").concat(value);
          }
        }
        function removeClass(element, value) {
          if (!value) {
            return;
          }
          if (isNumber(element.length)) {
            forEach(element, function(elem) {
              removeClass(elem, value);
            });
            return;
          }
          if (element.classList) {
            element.classList.remove(value);
            return;
          }
          if (element.className.indexOf(value) >= 0) {
            element.className = element.className.replace(value, "");
          }
        }
        function toggleClass(element, value, added) {
          if (!value) {
            return;
          }
          if (isNumber(element.length)) {
            forEach(element, function(elem) {
              toggleClass(elem, value, added);
            });
            return;
          }
          if (added) {
            addClass(element, value);
          } else {
            removeClass(element, value);
          }
        }
        var REGEXP_CAMEL_CASE = /([a-z\d])([A-Z])/g;
        function toParamCase(value) {
          return value.replace(REGEXP_CAMEL_CASE, "$1-$2").toLowerCase();
        }
        function getData(element, name) {
          if (isObject3(element[name])) {
            return element[name];
          }
          if (element.dataset) {
            return element.dataset[name];
          }
          return element.getAttribute("data-".concat(toParamCase(name)));
        }
        function setData(element, name, data) {
          if (isObject3(data)) {
            element[name] = data;
          } else if (element.dataset) {
            element.dataset[name] = data;
          } else {
            element.setAttribute("data-".concat(toParamCase(name)), data);
          }
        }
        function removeData(element, name) {
          if (isObject3(element[name])) {
            try {
              delete element[name];
            } catch (error) {
              element[name] = void 0;
            }
          } else if (element.dataset) {
            try {
              delete element.dataset[name];
            } catch (error) {
              element.dataset[name] = void 0;
            }
          } else {
            element.removeAttribute("data-".concat(toParamCase(name)));
          }
        }
        var REGEXP_SPACES = /\s\s*/;
        var onceSupported = function() {
          var supported2 = false;
          if (IS_BROWSER) {
            var once = false;
            var listener = function listener2() {
            };
            var options = Object.defineProperty({}, "once", {
              get: function get2() {
                supported2 = true;
                return once;
              },
              set: function set2(value) {
                once = value;
              }
            });
            WINDOW.addEventListener("test", listener, options);
            WINDOW.removeEventListener("test", listener, options);
          }
          return supported2;
        }();
        function removeListener(element, type, listener) {
          var options = arguments.length > 3 && arguments[3] !== void 0 ? arguments[3] : {};
          var handler = listener;
          type.trim().split(REGEXP_SPACES).forEach(function(event) {
            if (!onceSupported) {
              var listeners = element.listeners;
              if (listeners && listeners[event] && listeners[event][listener]) {
                handler = listeners[event][listener];
                delete listeners[event][listener];
                if (Object.keys(listeners[event]).length === 0) {
                  delete listeners[event];
                }
                if (Object.keys(listeners).length === 0) {
                  delete element.listeners;
                }
              }
            }
            element.removeEventListener(event, handler, options);
          });
        }
        function addListener(element, type, listener) {
          var options = arguments.length > 3 && arguments[3] !== void 0 ? arguments[3] : {};
          var _handler = listener;
          type.trim().split(REGEXP_SPACES).forEach(function(event) {
            if (options.once && !onceSupported) {
              var _element$listeners = element.listeners, listeners = _element$listeners === void 0 ? {} : _element$listeners;
              _handler = function handler() {
                delete listeners[event][listener];
                element.removeEventListener(event, _handler, options);
                for (var _len2 = arguments.length, args = new Array(_len2), _key2 = 0; _key2 < _len2; _key2++) {
                  args[_key2] = arguments[_key2];
                }
                listener.apply(element, args);
              };
              if (!listeners[event]) {
                listeners[event] = {};
              }
              if (listeners[event][listener]) {
                element.removeEventListener(event, listeners[event][listener], options);
              }
              listeners[event][listener] = _handler;
              element.listeners = listeners;
            }
            element.addEventListener(event, _handler, options);
          });
        }
        function dispatchEvent(element, type, data) {
          var event;
          if (isFunction3(Event) && isFunction3(CustomEvent)) {
            event = new CustomEvent(type, {
              detail: data,
              bubbles: true,
              cancelable: true
            });
          } else {
            event = document.createEvent("CustomEvent");
            event.initCustomEvent(type, true, true, data);
          }
          return element.dispatchEvent(event);
        }
        function getOffset(element) {
          var box = element.getBoundingClientRect();
          return {
            left: box.left + (window.pageXOffset - document.documentElement.clientLeft),
            top: box.top + (window.pageYOffset - document.documentElement.clientTop)
          };
        }
        var location = WINDOW.location;
        var REGEXP_ORIGINS = /^(\w+:)\/\/([^:/?#]*):?(\d*)/i;
        function isCrossOriginURL(url) {
          var parts = url.match(REGEXP_ORIGINS);
          return parts !== null && (parts[1] !== location.protocol || parts[2] !== location.hostname || parts[3] !== location.port);
        }
        function addTimestamp(url) {
          var timestamp = "timestamp=".concat(new Date().getTime());
          return url + (url.indexOf("?") === -1 ? "?" : "&") + timestamp;
        }
        function getTransforms(_ref) {
          var rotate = _ref.rotate, scaleX = _ref.scaleX, scaleY = _ref.scaleY, translateX = _ref.translateX, translateY = _ref.translateY;
          var values = [];
          if (isNumber(translateX) && translateX !== 0) {
            values.push("translateX(".concat(translateX, "px)"));
          }
          if (isNumber(translateY) && translateY !== 0) {
            values.push("translateY(".concat(translateY, "px)"));
          }
          if (isNumber(rotate) && rotate !== 0) {
            values.push("rotate(".concat(rotate, "deg)"));
          }
          if (isNumber(scaleX) && scaleX !== 1) {
            values.push("scaleX(".concat(scaleX, ")"));
          }
          if (isNumber(scaleY) && scaleY !== 1) {
            values.push("scaleY(".concat(scaleY, ")"));
          }
          var transform = values.length ? values.join(" ") : "none";
          return {
            WebkitTransform: transform,
            msTransform: transform,
            transform
          };
        }
        function getMaxZoomRatio(pointers) {
          var pointers2 = _objectSpread2({}, pointers);
          var maxRatio = 0;
          forEach(pointers, function(pointer, pointerId) {
            delete pointers2[pointerId];
            forEach(pointers2, function(pointer2) {
              var x1 = Math.abs(pointer.startX - pointer2.startX);
              var y1 = Math.abs(pointer.startY - pointer2.startY);
              var x2 = Math.abs(pointer.endX - pointer2.endX);
              var y2 = Math.abs(pointer.endY - pointer2.endY);
              var z1 = Math.sqrt(x1 * x1 + y1 * y1);
              var z2 = Math.sqrt(x2 * x2 + y2 * y2);
              var ratio = (z2 - z1) / z1;
              if (Math.abs(ratio) > Math.abs(maxRatio)) {
                maxRatio = ratio;
              }
            });
          });
          return maxRatio;
        }
        function getPointer(_ref2, endOnly) {
          var pageX = _ref2.pageX, pageY = _ref2.pageY;
          var end2 = {
            endX: pageX,
            endY: pageY
          };
          return endOnly ? end2 : _objectSpread2({
            startX: pageX,
            startY: pageY
          }, end2);
        }
        function getPointersCenter(pointers) {
          var pageX = 0;
          var pageY = 0;
          var count = 0;
          forEach(pointers, function(_ref3) {
            var startX = _ref3.startX, startY = _ref3.startY;
            pageX += startX;
            pageY += startY;
            count += 1;
          });
          pageX /= count;
          pageY /= count;
          return {
            pageX,
            pageY
          };
        }
        function getAdjustedSizes(_ref4) {
          var aspectRatio = _ref4.aspectRatio, height = _ref4.height, width = _ref4.width;
          var type = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : "contain";
          var isValidWidth = isPositiveNumber(width);
          var isValidHeight = isPositiveNumber(height);
          if (isValidWidth && isValidHeight) {
            var adjustedWidth = height * aspectRatio;
            if (type === "contain" && adjustedWidth > width || type === "cover" && adjustedWidth < width) {
              height = width / aspectRatio;
            } else {
              width = height * aspectRatio;
            }
          } else if (isValidWidth) {
            height = width / aspectRatio;
          } else if (isValidHeight) {
            width = height * aspectRatio;
          }
          return {
            width,
            height
          };
        }
        function getRotatedSizes(_ref5) {
          var width = _ref5.width, height = _ref5.height, degree = _ref5.degree;
          degree = Math.abs(degree) % 180;
          if (degree === 90) {
            return {
              width: height,
              height: width
            };
          }
          var arc = degree % 90 * Math.PI / 180;
          var sinArc = Math.sin(arc);
          var cosArc = Math.cos(arc);
          var newWidth = width * cosArc + height * sinArc;
          var newHeight = width * sinArc + height * cosArc;
          return degree > 90 ? {
            width: newHeight,
            height: newWidth
          } : {
            width: newWidth,
            height: newHeight
          };
        }
        function getSourceCanvas(image, _ref6, _ref7, _ref8) {
          var imageAspectRatio = _ref6.aspectRatio, imageNaturalWidth = _ref6.naturalWidth, imageNaturalHeight = _ref6.naturalHeight, _ref6$rotate = _ref6.rotate, rotate = _ref6$rotate === void 0 ? 0 : _ref6$rotate, _ref6$scaleX = _ref6.scaleX, scaleX = _ref6$scaleX === void 0 ? 1 : _ref6$scaleX, _ref6$scaleY = _ref6.scaleY, scaleY = _ref6$scaleY === void 0 ? 1 : _ref6$scaleY;
          var aspectRatio = _ref7.aspectRatio, naturalWidth = _ref7.naturalWidth, naturalHeight = _ref7.naturalHeight;
          var _ref8$fillColor = _ref8.fillColor, fillColor = _ref8$fillColor === void 0 ? "transparent" : _ref8$fillColor, _ref8$imageSmoothingE = _ref8.imageSmoothingEnabled, imageSmoothingEnabled = _ref8$imageSmoothingE === void 0 ? true : _ref8$imageSmoothingE, _ref8$imageSmoothingQ = _ref8.imageSmoothingQuality, imageSmoothingQuality = _ref8$imageSmoothingQ === void 0 ? "low" : _ref8$imageSmoothingQ, _ref8$maxWidth = _ref8.maxWidth, maxWidth = _ref8$maxWidth === void 0 ? Infinity : _ref8$maxWidth, _ref8$maxHeight = _ref8.maxHeight, maxHeight = _ref8$maxHeight === void 0 ? Infinity : _ref8$maxHeight, _ref8$minWidth = _ref8.minWidth, minWidth = _ref8$minWidth === void 0 ? 0 : _ref8$minWidth, _ref8$minHeight = _ref8.minHeight, minHeight = _ref8$minHeight === void 0 ? 0 : _ref8$minHeight;
          var canvas = document.createElement("canvas");
          var context = canvas.getContext("2d");
          var maxSizes = getAdjustedSizes({
            aspectRatio,
            width: maxWidth,
            height: maxHeight
          });
          var minSizes = getAdjustedSizes({
            aspectRatio,
            width: minWidth,
            height: minHeight
          }, "cover");
          var width = Math.min(maxSizes.width, Math.max(minSizes.width, naturalWidth));
          var height = Math.min(maxSizes.height, Math.max(minSizes.height, naturalHeight));
          var destMaxSizes = getAdjustedSizes({
            aspectRatio: imageAspectRatio,
            width: maxWidth,
            height: maxHeight
          });
          var destMinSizes = getAdjustedSizes({
            aspectRatio: imageAspectRatio,
            width: minWidth,
            height: minHeight
          }, "cover");
          var destWidth = Math.min(destMaxSizes.width, Math.max(destMinSizes.width, imageNaturalWidth));
          var destHeight = Math.min(destMaxSizes.height, Math.max(destMinSizes.height, imageNaturalHeight));
          var params = [-destWidth / 2, -destHeight / 2, destWidth, destHeight];
          canvas.width = normalizeDecimalNumber(width);
          canvas.height = normalizeDecimalNumber(height);
          context.fillStyle = fillColor;
          context.fillRect(0, 0, width, height);
          context.save();
          context.translate(width / 2, height / 2);
          context.rotate(rotate * Math.PI / 180);
          context.scale(scaleX, scaleY);
          context.imageSmoothingEnabled = imageSmoothingEnabled;
          context.imageSmoothingQuality = imageSmoothingQuality;
          context.drawImage.apply(context, [image].concat(_toConsumableArray(params.map(function(param) {
            return Math.floor(normalizeDecimalNumber(param));
          }))));
          context.restore();
          return canvas;
        }
        var fromCharCode = String.fromCharCode;
        function getStringFromCharCode(dataView, start2, length) {
          var str = "";
          length += start2;
          for (var i = start2; i < length; i += 1) {
            str += fromCharCode(dataView.getUint8(i));
          }
          return str;
        }
        var REGEXP_DATA_URL_HEAD = /^data:.*,/;
        function dataURLToArrayBuffer(dataURL) {
          var base64 = dataURL.replace(REGEXP_DATA_URL_HEAD, "");
          var binary = atob(base64);
          var arrayBuffer = new ArrayBuffer(binary.length);
          var uint8 = new Uint8Array(arrayBuffer);
          forEach(uint8, function(value, i) {
            uint8[i] = binary.charCodeAt(i);
          });
          return arrayBuffer;
        }
        function arrayBufferToDataURL(arrayBuffer, mimeType) {
          var chunks = [];
          var chunkSize = 8192;
          var uint8 = new Uint8Array(arrayBuffer);
          while (uint8.length > 0) {
            chunks.push(fromCharCode.apply(null, toArray(uint8.subarray(0, chunkSize))));
            uint8 = uint8.subarray(chunkSize);
          }
          return "data:".concat(mimeType, ";base64,").concat(btoa(chunks.join("")));
        }
        function resetAndGetOrientation(arrayBuffer) {
          var dataView = new DataView(arrayBuffer);
          var orientation;
          try {
            var littleEndian;
            var app1Start;
            var ifdStart;
            if (dataView.getUint8(0) === 255 && dataView.getUint8(1) === 216) {
              var length = dataView.byteLength;
              var offset2 = 2;
              while (offset2 + 1 < length) {
                if (dataView.getUint8(offset2) === 255 && dataView.getUint8(offset2 + 1) === 225) {
                  app1Start = offset2;
                  break;
                }
                offset2 += 1;
              }
            }
            if (app1Start) {
              var exifIDCode = app1Start + 4;
              var tiffOffset = app1Start + 10;
              if (getStringFromCharCode(dataView, exifIDCode, 4) === "Exif") {
                var endianness = dataView.getUint16(tiffOffset);
                littleEndian = endianness === 18761;
                if (littleEndian || endianness === 19789) {
                  if (dataView.getUint16(tiffOffset + 2, littleEndian) === 42) {
                    var firstIFDOffset = dataView.getUint32(tiffOffset + 4, littleEndian);
                    if (firstIFDOffset >= 8) {
                      ifdStart = tiffOffset + firstIFDOffset;
                    }
                  }
                }
              }
            }
            if (ifdStart) {
              var _length = dataView.getUint16(ifdStart, littleEndian);
              var _offset;
              var i;
              for (i = 0; i < _length; i += 1) {
                _offset = ifdStart + i * 12 + 2;
                if (dataView.getUint16(_offset, littleEndian) === 274) {
                  _offset += 8;
                  orientation = dataView.getUint16(_offset, littleEndian);
                  dataView.setUint16(_offset, 1, littleEndian);
                  break;
                }
              }
            }
          } catch (error) {
            orientation = 1;
          }
          return orientation;
        }
        function parseOrientation(orientation) {
          var rotate = 0;
          var scaleX = 1;
          var scaleY = 1;
          switch (orientation) {
            case 2:
              scaleX = -1;
              break;
            case 3:
              rotate = -180;
              break;
            case 4:
              scaleY = -1;
              break;
            case 5:
              rotate = 90;
              scaleY = -1;
              break;
            case 6:
              rotate = 90;
              break;
            case 7:
              rotate = 90;
              scaleX = -1;
              break;
            case 8:
              rotate = -90;
              break;
          }
          return {
            rotate,
            scaleX,
            scaleY
          };
        }
        var render8 = {
          render: function render9() {
            this.initContainer();
            this.initCanvas();
            this.initCropBox();
            this.renderCanvas();
            if (this.cropped) {
              this.renderCropBox();
            }
          },
          initContainer: function initContainer() {
            var element = this.element, options = this.options, container = this.container, cropper = this.cropper;
            var minWidth = Number(options.minContainerWidth);
            var minHeight = Number(options.minContainerHeight);
            addClass(cropper, CLASS_HIDDEN);
            removeClass(element, CLASS_HIDDEN);
            var containerData = {
              width: Math.max(container.offsetWidth, minWidth >= 0 ? minWidth : MIN_CONTAINER_WIDTH),
              height: Math.max(container.offsetHeight, minHeight >= 0 ? minHeight : MIN_CONTAINER_HEIGHT)
            };
            this.containerData = containerData;
            setStyle2(cropper, {
              width: containerData.width,
              height: containerData.height
            });
            addClass(element, CLASS_HIDDEN);
            removeClass(cropper, CLASS_HIDDEN);
          },
          initCanvas: function initCanvas() {
            var containerData = this.containerData, imageData = this.imageData;
            var viewMode = this.options.viewMode;
            var rotated = Math.abs(imageData.rotate) % 180 === 90;
            var naturalWidth = rotated ? imageData.naturalHeight : imageData.naturalWidth;
            var naturalHeight = rotated ? imageData.naturalWidth : imageData.naturalHeight;
            var aspectRatio = naturalWidth / naturalHeight;
            var canvasWidth = containerData.width;
            var canvasHeight = containerData.height;
            if (containerData.height * aspectRatio > containerData.width) {
              if (viewMode === 3) {
                canvasWidth = containerData.height * aspectRatio;
              } else {
                canvasHeight = containerData.width / aspectRatio;
              }
            } else if (viewMode === 3) {
              canvasHeight = containerData.width / aspectRatio;
            } else {
              canvasWidth = containerData.height * aspectRatio;
            }
            var canvasData = {
              aspectRatio,
              naturalWidth,
              naturalHeight,
              width: canvasWidth,
              height: canvasHeight
            };
            this.canvasData = canvasData;
            this.limited = viewMode === 1 || viewMode === 2;
            this.limitCanvas(true, true);
            canvasData.width = Math.min(Math.max(canvasData.width, canvasData.minWidth), canvasData.maxWidth);
            canvasData.height = Math.min(Math.max(canvasData.height, canvasData.minHeight), canvasData.maxHeight);
            canvasData.left = (containerData.width - canvasData.width) / 2;
            canvasData.top = (containerData.height - canvasData.height) / 2;
            canvasData.oldLeft = canvasData.left;
            canvasData.oldTop = canvasData.top;
            this.initialCanvasData = assign({}, canvasData);
          },
          limitCanvas: function limitCanvas(sizeLimited, positionLimited) {
            var options = this.options, containerData = this.containerData, canvasData = this.canvasData, cropBoxData = this.cropBoxData;
            var viewMode = options.viewMode;
            var aspectRatio = canvasData.aspectRatio;
            var cropped = this.cropped && cropBoxData;
            if (sizeLimited) {
              var minCanvasWidth = Number(options.minCanvasWidth) || 0;
              var minCanvasHeight = Number(options.minCanvasHeight) || 0;
              if (viewMode > 1) {
                minCanvasWidth = Math.max(minCanvasWidth, containerData.width);
                minCanvasHeight = Math.max(minCanvasHeight, containerData.height);
                if (viewMode === 3) {
                  if (minCanvasHeight * aspectRatio > minCanvasWidth) {
                    minCanvasWidth = minCanvasHeight * aspectRatio;
                  } else {
                    minCanvasHeight = minCanvasWidth / aspectRatio;
                  }
                }
              } else if (viewMode > 0) {
                if (minCanvasWidth) {
                  minCanvasWidth = Math.max(minCanvasWidth, cropped ? cropBoxData.width : 0);
                } else if (minCanvasHeight) {
                  minCanvasHeight = Math.max(minCanvasHeight, cropped ? cropBoxData.height : 0);
                } else if (cropped) {
                  minCanvasWidth = cropBoxData.width;
                  minCanvasHeight = cropBoxData.height;
                  if (minCanvasHeight * aspectRatio > minCanvasWidth) {
                    minCanvasWidth = minCanvasHeight * aspectRatio;
                  } else {
                    minCanvasHeight = minCanvasWidth / aspectRatio;
                  }
                }
              }
              var _getAdjustedSizes = getAdjustedSizes({
                aspectRatio,
                width: minCanvasWidth,
                height: minCanvasHeight
              });
              minCanvasWidth = _getAdjustedSizes.width;
              minCanvasHeight = _getAdjustedSizes.height;
              canvasData.minWidth = minCanvasWidth;
              canvasData.minHeight = minCanvasHeight;
              canvasData.maxWidth = Infinity;
              canvasData.maxHeight = Infinity;
            }
            if (positionLimited) {
              if (viewMode > (cropped ? 0 : 1)) {
                var newCanvasLeft = containerData.width - canvasData.width;
                var newCanvasTop = containerData.height - canvasData.height;
                canvasData.minLeft = Math.min(0, newCanvasLeft);
                canvasData.minTop = Math.min(0, newCanvasTop);
                canvasData.maxLeft = Math.max(0, newCanvasLeft);
                canvasData.maxTop = Math.max(0, newCanvasTop);
                if (cropped && this.limited) {
                  canvasData.minLeft = Math.min(cropBoxData.left, cropBoxData.left + (cropBoxData.width - canvasData.width));
                  canvasData.minTop = Math.min(cropBoxData.top, cropBoxData.top + (cropBoxData.height - canvasData.height));
                  canvasData.maxLeft = cropBoxData.left;
                  canvasData.maxTop = cropBoxData.top;
                  if (viewMode === 2) {
                    if (canvasData.width >= containerData.width) {
                      canvasData.minLeft = Math.min(0, newCanvasLeft);
                      canvasData.maxLeft = Math.max(0, newCanvasLeft);
                    }
                    if (canvasData.height >= containerData.height) {
                      canvasData.minTop = Math.min(0, newCanvasTop);
                      canvasData.maxTop = Math.max(0, newCanvasTop);
                    }
                  }
                }
              } else {
                canvasData.minLeft = -canvasData.width;
                canvasData.minTop = -canvasData.height;
                canvasData.maxLeft = containerData.width;
                canvasData.maxTop = containerData.height;
              }
            }
          },
          renderCanvas: function renderCanvas(changed, transformed) {
            var canvasData = this.canvasData, imageData = this.imageData;
            if (transformed) {
              var _getRotatedSizes = getRotatedSizes({
                width: imageData.naturalWidth * Math.abs(imageData.scaleX || 1),
                height: imageData.naturalHeight * Math.abs(imageData.scaleY || 1),
                degree: imageData.rotate || 0
              }), naturalWidth = _getRotatedSizes.width, naturalHeight = _getRotatedSizes.height;
              var width = canvasData.width * (naturalWidth / canvasData.naturalWidth);
              var height = canvasData.height * (naturalHeight / canvasData.naturalHeight);
              canvasData.left -= (width - canvasData.width) / 2;
              canvasData.top -= (height - canvasData.height) / 2;
              canvasData.width = width;
              canvasData.height = height;
              canvasData.aspectRatio = naturalWidth / naturalHeight;
              canvasData.naturalWidth = naturalWidth;
              canvasData.naturalHeight = naturalHeight;
              this.limitCanvas(true, false);
            }
            if (canvasData.width > canvasData.maxWidth || canvasData.width < canvasData.minWidth) {
              canvasData.left = canvasData.oldLeft;
            }
            if (canvasData.height > canvasData.maxHeight || canvasData.height < canvasData.minHeight) {
              canvasData.top = canvasData.oldTop;
            }
            canvasData.width = Math.min(Math.max(canvasData.width, canvasData.minWidth), canvasData.maxWidth);
            canvasData.height = Math.min(Math.max(canvasData.height, canvasData.minHeight), canvasData.maxHeight);
            this.limitCanvas(false, true);
            canvasData.left = Math.min(Math.max(canvasData.left, canvasData.minLeft), canvasData.maxLeft);
            canvasData.top = Math.min(Math.max(canvasData.top, canvasData.minTop), canvasData.maxTop);
            canvasData.oldLeft = canvasData.left;
            canvasData.oldTop = canvasData.top;
            setStyle2(this.canvas, assign({
              width: canvasData.width,
              height: canvasData.height
            }, getTransforms({
              translateX: canvasData.left,
              translateY: canvasData.top
            })));
            this.renderImage(changed);
            if (this.cropped && this.limited) {
              this.limitCropBox(true, true);
            }
          },
          renderImage: function renderImage(changed) {
            var canvasData = this.canvasData, imageData = this.imageData;
            var width = imageData.naturalWidth * (canvasData.width / canvasData.naturalWidth);
            var height = imageData.naturalHeight * (canvasData.height / canvasData.naturalHeight);
            assign(imageData, {
              width,
              height,
              left: (canvasData.width - width) / 2,
              top: (canvasData.height - height) / 2
            });
            setStyle2(this.image, assign({
              width: imageData.width,
              height: imageData.height
            }, getTransforms(assign({
              translateX: imageData.left,
              translateY: imageData.top
            }, imageData))));
            if (changed) {
              this.output();
            }
          },
          initCropBox: function initCropBox() {
            var options = this.options, canvasData = this.canvasData;
            var aspectRatio = options.aspectRatio || options.initialAspectRatio;
            var autoCropArea = Number(options.autoCropArea) || 0.8;
            var cropBoxData = {
              width: canvasData.width,
              height: canvasData.height
            };
            if (aspectRatio) {
              if (canvasData.height * aspectRatio > canvasData.width) {
                cropBoxData.height = cropBoxData.width / aspectRatio;
              } else {
                cropBoxData.width = cropBoxData.height * aspectRatio;
              }
            }
            this.cropBoxData = cropBoxData;
            this.limitCropBox(true, true);
            cropBoxData.width = Math.min(Math.max(cropBoxData.width, cropBoxData.minWidth), cropBoxData.maxWidth);
            cropBoxData.height = Math.min(Math.max(cropBoxData.height, cropBoxData.minHeight), cropBoxData.maxHeight);
            cropBoxData.width = Math.max(cropBoxData.minWidth, cropBoxData.width * autoCropArea);
            cropBoxData.height = Math.max(cropBoxData.minHeight, cropBoxData.height * autoCropArea);
            cropBoxData.left = canvasData.left + (canvasData.width - cropBoxData.width) / 2;
            cropBoxData.top = canvasData.top + (canvasData.height - cropBoxData.height) / 2;
            cropBoxData.oldLeft = cropBoxData.left;
            cropBoxData.oldTop = cropBoxData.top;
            this.initialCropBoxData = assign({}, cropBoxData);
          },
          limitCropBox: function limitCropBox(sizeLimited, positionLimited) {
            var options = this.options, containerData = this.containerData, canvasData = this.canvasData, cropBoxData = this.cropBoxData, limited = this.limited;
            var aspectRatio = options.aspectRatio;
            if (sizeLimited) {
              var minCropBoxWidth = Number(options.minCropBoxWidth) || 0;
              var minCropBoxHeight = Number(options.minCropBoxHeight) || 0;
              var maxCropBoxWidth = limited ? Math.min(containerData.width, canvasData.width, canvasData.width + canvasData.left, containerData.width - canvasData.left) : containerData.width;
              var maxCropBoxHeight = limited ? Math.min(containerData.height, canvasData.height, canvasData.height + canvasData.top, containerData.height - canvasData.top) : containerData.height;
              minCropBoxWidth = Math.min(minCropBoxWidth, containerData.width);
              minCropBoxHeight = Math.min(minCropBoxHeight, containerData.height);
              if (aspectRatio) {
                if (minCropBoxWidth && minCropBoxHeight) {
                  if (minCropBoxHeight * aspectRatio > minCropBoxWidth) {
                    minCropBoxHeight = minCropBoxWidth / aspectRatio;
                  } else {
                    minCropBoxWidth = minCropBoxHeight * aspectRatio;
                  }
                } else if (minCropBoxWidth) {
                  minCropBoxHeight = minCropBoxWidth / aspectRatio;
                } else if (minCropBoxHeight) {
                  minCropBoxWidth = minCropBoxHeight * aspectRatio;
                }
                if (maxCropBoxHeight * aspectRatio > maxCropBoxWidth) {
                  maxCropBoxHeight = maxCropBoxWidth / aspectRatio;
                } else {
                  maxCropBoxWidth = maxCropBoxHeight * aspectRatio;
                }
              }
              cropBoxData.minWidth = Math.min(minCropBoxWidth, maxCropBoxWidth);
              cropBoxData.minHeight = Math.min(minCropBoxHeight, maxCropBoxHeight);
              cropBoxData.maxWidth = maxCropBoxWidth;
              cropBoxData.maxHeight = maxCropBoxHeight;
            }
            if (positionLimited) {
              if (limited) {
                cropBoxData.minLeft = Math.max(0, canvasData.left);
                cropBoxData.minTop = Math.max(0, canvasData.top);
                cropBoxData.maxLeft = Math.min(containerData.width, canvasData.left + canvasData.width) - cropBoxData.width;
                cropBoxData.maxTop = Math.min(containerData.height, canvasData.top + canvasData.height) - cropBoxData.height;
              } else {
                cropBoxData.minLeft = 0;
                cropBoxData.minTop = 0;
                cropBoxData.maxLeft = containerData.width - cropBoxData.width;
                cropBoxData.maxTop = containerData.height - cropBoxData.height;
              }
            }
          },
          renderCropBox: function renderCropBox() {
            var options = this.options, containerData = this.containerData, cropBoxData = this.cropBoxData;
            if (cropBoxData.width > cropBoxData.maxWidth || cropBoxData.width < cropBoxData.minWidth) {
              cropBoxData.left = cropBoxData.oldLeft;
            }
            if (cropBoxData.height > cropBoxData.maxHeight || cropBoxData.height < cropBoxData.minHeight) {
              cropBoxData.top = cropBoxData.oldTop;
            }
            cropBoxData.width = Math.min(Math.max(cropBoxData.width, cropBoxData.minWidth), cropBoxData.maxWidth);
            cropBoxData.height = Math.min(Math.max(cropBoxData.height, cropBoxData.minHeight), cropBoxData.maxHeight);
            this.limitCropBox(false, true);
            cropBoxData.left = Math.min(Math.max(cropBoxData.left, cropBoxData.minLeft), cropBoxData.maxLeft);
            cropBoxData.top = Math.min(Math.max(cropBoxData.top, cropBoxData.minTop), cropBoxData.maxTop);
            cropBoxData.oldLeft = cropBoxData.left;
            cropBoxData.oldTop = cropBoxData.top;
            if (options.movable && options.cropBoxMovable) {
              setData(this.face, DATA_ACTION, cropBoxData.width >= containerData.width && cropBoxData.height >= containerData.height ? ACTION_MOVE : ACTION_ALL);
            }
            setStyle2(this.cropBox, assign({
              width: cropBoxData.width,
              height: cropBoxData.height
            }, getTransforms({
              translateX: cropBoxData.left,
              translateY: cropBoxData.top
            })));
            if (this.cropped && this.limited) {
              this.limitCanvas(true, true);
            }
            if (!this.disabled) {
              this.output();
            }
          },
          output: function output() {
            this.preview();
            dispatchEvent(this.element, EVENT_CROP, this.getData());
          }
        };
        var preview = {
          initPreview: function initPreview() {
            var element = this.element, crossOrigin = this.crossOrigin;
            var preview2 = this.options.preview;
            var url = crossOrigin ? this.crossOriginUrl : this.url;
            var alt = element.alt || "The image to preview";
            var image = document.createElement("img");
            if (crossOrigin) {
              image.crossOrigin = crossOrigin;
            }
            image.src = url;
            image.alt = alt;
            this.viewBox.appendChild(image);
            this.viewBoxImage = image;
            if (!preview2) {
              return;
            }
            var previews = preview2;
            if (typeof preview2 === "string") {
              previews = element.ownerDocument.querySelectorAll(preview2);
            } else if (preview2.querySelector) {
              previews = [preview2];
            }
            this.previews = previews;
            forEach(previews, function(el) {
              var img = document.createElement("img");
              setData(el, DATA_PREVIEW, {
                width: el.offsetWidth,
                height: el.offsetHeight,
                html: el.innerHTML
              });
              if (crossOrigin) {
                img.crossOrigin = crossOrigin;
              }
              img.src = url;
              img.alt = alt;
              img.style.cssText = 'display:block;width:100%;height:auto;min-width:0!important;min-height:0!important;max-width:none!important;max-height:none!important;image-orientation:0deg!important;"';
              el.innerHTML = "";
              el.appendChild(img);
            });
          },
          resetPreview: function resetPreview() {
            forEach(this.previews, function(element) {
              var data = getData(element, DATA_PREVIEW);
              setStyle2(element, {
                width: data.width,
                height: data.height
              });
              element.innerHTML = data.html;
              removeData(element, DATA_PREVIEW);
            });
          },
          preview: function preview2() {
            var imageData = this.imageData, canvasData = this.canvasData, cropBoxData = this.cropBoxData;
            var cropBoxWidth = cropBoxData.width, cropBoxHeight = cropBoxData.height;
            var width = imageData.width, height = imageData.height;
            var left2 = cropBoxData.left - canvasData.left - imageData.left;
            var top2 = cropBoxData.top - canvasData.top - imageData.top;
            if (!this.cropped || this.disabled) {
              return;
            }
            setStyle2(this.viewBoxImage, assign({
              width,
              height
            }, getTransforms(assign({
              translateX: -left2,
              translateY: -top2
            }, imageData))));
            forEach(this.previews, function(element) {
              var data = getData(element, DATA_PREVIEW);
              var originalWidth = data.width;
              var originalHeight = data.height;
              var newWidth = originalWidth;
              var newHeight = originalHeight;
              var ratio = 1;
              if (cropBoxWidth) {
                ratio = originalWidth / cropBoxWidth;
                newHeight = cropBoxHeight * ratio;
              }
              if (cropBoxHeight && newHeight > originalHeight) {
                ratio = originalHeight / cropBoxHeight;
                newWidth = cropBoxWidth * ratio;
                newHeight = originalHeight;
              }
              setStyle2(element, {
                width: newWidth,
                height: newHeight
              });
              setStyle2(element.getElementsByTagName("img")[0], assign({
                width: width * ratio,
                height: height * ratio
              }, getTransforms(assign({
                translateX: -left2 * ratio,
                translateY: -top2 * ratio
              }, imageData))));
            });
          }
        };
        var events = {
          bind: function bind() {
            var element = this.element, options = this.options, cropper = this.cropper;
            if (isFunction3(options.cropstart)) {
              addListener(element, EVENT_CROP_START, options.cropstart);
            }
            if (isFunction3(options.cropmove)) {
              addListener(element, EVENT_CROP_MOVE, options.cropmove);
            }
            if (isFunction3(options.cropend)) {
              addListener(element, EVENT_CROP_END, options.cropend);
            }
            if (isFunction3(options.crop)) {
              addListener(element, EVENT_CROP, options.crop);
            }
            if (isFunction3(options.zoom)) {
              addListener(element, EVENT_ZOOM, options.zoom);
            }
            addListener(cropper, EVENT_POINTER_DOWN, this.onCropStart = this.cropStart.bind(this));
            if (options.zoomable && options.zoomOnWheel) {
              addListener(cropper, EVENT_WHEEL, this.onWheel = this.wheel.bind(this), {
                passive: false,
                capture: true
              });
            }
            if (options.toggleDragModeOnDblclick) {
              addListener(cropper, EVENT_DBLCLICK, this.onDblclick = this.dblclick.bind(this));
            }
            addListener(element.ownerDocument, EVENT_POINTER_MOVE, this.onCropMove = this.cropMove.bind(this));
            addListener(element.ownerDocument, EVENT_POINTER_UP, this.onCropEnd = this.cropEnd.bind(this));
            if (options.responsive) {
              addListener(window, EVENT_RESIZE, this.onResize = this.resize.bind(this));
            }
          },
          unbind: function unbind() {
            var element = this.element, options = this.options, cropper = this.cropper;
            if (isFunction3(options.cropstart)) {
              removeListener(element, EVENT_CROP_START, options.cropstart);
            }
            if (isFunction3(options.cropmove)) {
              removeListener(element, EVENT_CROP_MOVE, options.cropmove);
            }
            if (isFunction3(options.cropend)) {
              removeListener(element, EVENT_CROP_END, options.cropend);
            }
            if (isFunction3(options.crop)) {
              removeListener(element, EVENT_CROP, options.crop);
            }
            if (isFunction3(options.zoom)) {
              removeListener(element, EVENT_ZOOM, options.zoom);
            }
            removeListener(cropper, EVENT_POINTER_DOWN, this.onCropStart);
            if (options.zoomable && options.zoomOnWheel) {
              removeListener(cropper, EVENT_WHEEL, this.onWheel, {
                passive: false,
                capture: true
              });
            }
            if (options.toggleDragModeOnDblclick) {
              removeListener(cropper, EVENT_DBLCLICK, this.onDblclick);
            }
            removeListener(element.ownerDocument, EVENT_POINTER_MOVE, this.onCropMove);
            removeListener(element.ownerDocument, EVENT_POINTER_UP, this.onCropEnd);
            if (options.responsive) {
              removeListener(window, EVENT_RESIZE, this.onResize);
            }
          }
        };
        var handlers = {
          resize: function resize() {
            if (this.disabled) {
              return;
            }
            var options = this.options, container = this.container, containerData = this.containerData;
            var ratioX = container.offsetWidth / containerData.width;
            var ratioY = container.offsetHeight / containerData.height;
            var ratio = Math.abs(ratioX - 1) > Math.abs(ratioY - 1) ? ratioX : ratioY;
            if (ratio !== 1) {
              var canvasData;
              var cropBoxData;
              if (options.restore) {
                canvasData = this.getCanvasData();
                cropBoxData = this.getCropBoxData();
              }
              this.render();
              if (options.restore) {
                this.setCanvasData(forEach(canvasData, function(n, i) {
                  canvasData[i] = n * ratio;
                }));
                this.setCropBoxData(forEach(cropBoxData, function(n, i) {
                  cropBoxData[i] = n * ratio;
                }));
              }
            }
          },
          dblclick: function dblclick() {
            if (this.disabled || this.options.dragMode === DRAG_MODE_NONE) {
              return;
            }
            this.setDragMode(hasClass(this.dragBox, CLASS_CROP) ? DRAG_MODE_MOVE : DRAG_MODE_CROP);
          },
          wheel: function wheel(event) {
            var _this = this;
            var ratio = Number(this.options.wheelZoomRatio) || 0.1;
            var delta = 1;
            if (this.disabled) {
              return;
            }
            event.preventDefault();
            if (this.wheeling) {
              return;
            }
            this.wheeling = true;
            setTimeout(function() {
              _this.wheeling = false;
            }, 50);
            if (event.deltaY) {
              delta = event.deltaY > 0 ? 1 : -1;
            } else if (event.wheelDelta) {
              delta = -event.wheelDelta / 120;
            } else if (event.detail) {
              delta = event.detail > 0 ? 1 : -1;
            }
            this.zoom(-delta * ratio, event);
          },
          cropStart: function cropStart(event) {
            var buttons = event.buttons, button = event.button;
            if (this.disabled || (event.type === "mousedown" || event.type === "pointerdown" && event.pointerType === "mouse") && (isNumber(buttons) && buttons !== 1 || isNumber(button) && button !== 0 || event.ctrlKey)) {
              return;
            }
            var options = this.options, pointers = this.pointers;
            var action;
            if (event.changedTouches) {
              forEach(event.changedTouches, function(touch) {
                pointers[touch.identifier] = getPointer(touch);
              });
            } else {
              pointers[event.pointerId || 0] = getPointer(event);
            }
            if (Object.keys(pointers).length > 1 && options.zoomable && options.zoomOnTouch) {
              action = ACTION_ZOOM;
            } else {
              action = getData(event.target, DATA_ACTION);
            }
            if (!REGEXP_ACTIONS.test(action)) {
              return;
            }
            if (dispatchEvent(this.element, EVENT_CROP_START, {
              originalEvent: event,
              action
            }) === false) {
              return;
            }
            event.preventDefault();
            this.action = action;
            this.cropping = false;
            if (action === ACTION_CROP) {
              this.cropping = true;
              addClass(this.dragBox, CLASS_MODAL);
            }
          },
          cropMove: function cropMove(event) {
            var action = this.action;
            if (this.disabled || !action) {
              return;
            }
            var pointers = this.pointers;
            event.preventDefault();
            if (dispatchEvent(this.element, EVENT_CROP_MOVE, {
              originalEvent: event,
              action
            }) === false) {
              return;
            }
            if (event.changedTouches) {
              forEach(event.changedTouches, function(touch) {
                assign(pointers[touch.identifier] || {}, getPointer(touch, true));
              });
            } else {
              assign(pointers[event.pointerId || 0] || {}, getPointer(event, true));
            }
            this.change(event);
          },
          cropEnd: function cropEnd(event) {
            if (this.disabled) {
              return;
            }
            var action = this.action, pointers = this.pointers;
            if (event.changedTouches) {
              forEach(event.changedTouches, function(touch) {
                delete pointers[touch.identifier];
              });
            } else {
              delete pointers[event.pointerId || 0];
            }
            if (!action) {
              return;
            }
            event.preventDefault();
            if (!Object.keys(pointers).length) {
              this.action = "";
            }
            if (this.cropping) {
              this.cropping = false;
              toggleClass(this.dragBox, CLASS_MODAL, this.cropped && this.options.modal);
            }
            dispatchEvent(this.element, EVENT_CROP_END, {
              originalEvent: event,
              action
            });
          }
        };
        var change = {
          change: function change2(event) {
            var options = this.options, canvasData = this.canvasData, containerData = this.containerData, cropBoxData = this.cropBoxData, pointers = this.pointers;
            var action = this.action;
            var aspectRatio = options.aspectRatio;
            var left2 = cropBoxData.left, top2 = cropBoxData.top, width = cropBoxData.width, height = cropBoxData.height;
            var right2 = left2 + width;
            var bottom2 = top2 + height;
            var minLeft = 0;
            var minTop = 0;
            var maxWidth = containerData.width;
            var maxHeight = containerData.height;
            var renderable = true;
            var offset2;
            if (!aspectRatio && event.shiftKey) {
              aspectRatio = width && height ? width / height : 1;
            }
            if (this.limited) {
              minLeft = cropBoxData.minLeft;
              minTop = cropBoxData.minTop;
              maxWidth = minLeft + Math.min(containerData.width, canvasData.width, canvasData.left + canvasData.width);
              maxHeight = minTop + Math.min(containerData.height, canvasData.height, canvasData.top + canvasData.height);
            }
            var pointer = pointers[Object.keys(pointers)[0]];
            var range = {
              x: pointer.endX - pointer.startX,
              y: pointer.endY - pointer.startY
            };
            var check = function check2(side) {
              switch (side) {
                case ACTION_EAST:
                  if (right2 + range.x > maxWidth) {
                    range.x = maxWidth - right2;
                  }
                  break;
                case ACTION_WEST:
                  if (left2 + range.x < minLeft) {
                    range.x = minLeft - left2;
                  }
                  break;
                case ACTION_NORTH:
                  if (top2 + range.y < minTop) {
                    range.y = minTop - top2;
                  }
                  break;
                case ACTION_SOUTH:
                  if (bottom2 + range.y > maxHeight) {
                    range.y = maxHeight - bottom2;
                  }
                  break;
              }
            };
            switch (action) {
              case ACTION_ALL:
                left2 += range.x;
                top2 += range.y;
                break;
              case ACTION_EAST:
                if (range.x >= 0 && (right2 >= maxWidth || aspectRatio && (top2 <= minTop || bottom2 >= maxHeight))) {
                  renderable = false;
                  break;
                }
                check(ACTION_EAST);
                width += range.x;
                if (width < 0) {
                  action = ACTION_WEST;
                  width = -width;
                  left2 -= width;
                }
                if (aspectRatio) {
                  height = width / aspectRatio;
                  top2 += (cropBoxData.height - height) / 2;
                }
                break;
              case ACTION_NORTH:
                if (range.y <= 0 && (top2 <= minTop || aspectRatio && (left2 <= minLeft || right2 >= maxWidth))) {
                  renderable = false;
                  break;
                }
                check(ACTION_NORTH);
                height -= range.y;
                top2 += range.y;
                if (height < 0) {
                  action = ACTION_SOUTH;
                  height = -height;
                  top2 -= height;
                }
                if (aspectRatio) {
                  width = height * aspectRatio;
                  left2 += (cropBoxData.width - width) / 2;
                }
                break;
              case ACTION_WEST:
                if (range.x <= 0 && (left2 <= minLeft || aspectRatio && (top2 <= minTop || bottom2 >= maxHeight))) {
                  renderable = false;
                  break;
                }
                check(ACTION_WEST);
                width -= range.x;
                left2 += range.x;
                if (width < 0) {
                  action = ACTION_EAST;
                  width = -width;
                  left2 -= width;
                }
                if (aspectRatio) {
                  height = width / aspectRatio;
                  top2 += (cropBoxData.height - height) / 2;
                }
                break;
              case ACTION_SOUTH:
                if (range.y >= 0 && (bottom2 >= maxHeight || aspectRatio && (left2 <= minLeft || right2 >= maxWidth))) {
                  renderable = false;
                  break;
                }
                check(ACTION_SOUTH);
                height += range.y;
                if (height < 0) {
                  action = ACTION_NORTH;
                  height = -height;
                  top2 -= height;
                }
                if (aspectRatio) {
                  width = height * aspectRatio;
                  left2 += (cropBoxData.width - width) / 2;
                }
                break;
              case ACTION_NORTH_EAST:
                if (aspectRatio) {
                  if (range.y <= 0 && (top2 <= minTop || right2 >= maxWidth)) {
                    renderable = false;
                    break;
                  }
                  check(ACTION_NORTH);
                  height -= range.y;
                  top2 += range.y;
                  width = height * aspectRatio;
                } else {
                  check(ACTION_NORTH);
                  check(ACTION_EAST);
                  if (range.x >= 0) {
                    if (right2 < maxWidth) {
                      width += range.x;
                    } else if (range.y <= 0 && top2 <= minTop) {
                      renderable = false;
                    }
                  } else {
                    width += range.x;
                  }
                  if (range.y <= 0) {
                    if (top2 > minTop) {
                      height -= range.y;
                      top2 += range.y;
                    }
                  } else {
                    height -= range.y;
                    top2 += range.y;
                  }
                }
                if (width < 0 && height < 0) {
                  action = ACTION_SOUTH_WEST;
                  height = -height;
                  width = -width;
                  top2 -= height;
                  left2 -= width;
                } else if (width < 0) {
                  action = ACTION_NORTH_WEST;
                  width = -width;
                  left2 -= width;
                } else if (height < 0) {
                  action = ACTION_SOUTH_EAST;
                  height = -height;
                  top2 -= height;
                }
                break;
              case ACTION_NORTH_WEST:
                if (aspectRatio) {
                  if (range.y <= 0 && (top2 <= minTop || left2 <= minLeft)) {
                    renderable = false;
                    break;
                  }
                  check(ACTION_NORTH);
                  height -= range.y;
                  top2 += range.y;
                  width = height * aspectRatio;
                  left2 += cropBoxData.width - width;
                } else {
                  check(ACTION_NORTH);
                  check(ACTION_WEST);
                  if (range.x <= 0) {
                    if (left2 > minLeft) {
                      width -= range.x;
                      left2 += range.x;
                    } else if (range.y <= 0 && top2 <= minTop) {
                      renderable = false;
                    }
                  } else {
                    width -= range.x;
                    left2 += range.x;
                  }
                  if (range.y <= 0) {
                    if (top2 > minTop) {
                      height -= range.y;
                      top2 += range.y;
                    }
                  } else {
                    height -= range.y;
                    top2 += range.y;
                  }
                }
                if (width < 0 && height < 0) {
                  action = ACTION_SOUTH_EAST;
                  height = -height;
                  width = -width;
                  top2 -= height;
                  left2 -= width;
                } else if (width < 0) {
                  action = ACTION_NORTH_EAST;
                  width = -width;
                  left2 -= width;
                } else if (height < 0) {
                  action = ACTION_SOUTH_WEST;
                  height = -height;
                  top2 -= height;
                }
                break;
              case ACTION_SOUTH_WEST:
                if (aspectRatio) {
                  if (range.x <= 0 && (left2 <= minLeft || bottom2 >= maxHeight)) {
                    renderable = false;
                    break;
                  }
                  check(ACTION_WEST);
                  width -= range.x;
                  left2 += range.x;
                  height = width / aspectRatio;
                } else {
                  check(ACTION_SOUTH);
                  check(ACTION_WEST);
                  if (range.x <= 0) {
                    if (left2 > minLeft) {
                      width -= range.x;
                      left2 += range.x;
                    } else if (range.y >= 0 && bottom2 >= maxHeight) {
                      renderable = false;
                    }
                  } else {
                    width -= range.x;
                    left2 += range.x;
                  }
                  if (range.y >= 0) {
                    if (bottom2 < maxHeight) {
                      height += range.y;
                    }
                  } else {
                    height += range.y;
                  }
                }
                if (width < 0 && height < 0) {
                  action = ACTION_NORTH_EAST;
                  height = -height;
                  width = -width;
                  top2 -= height;
                  left2 -= width;
                } else if (width < 0) {
                  action = ACTION_SOUTH_EAST;
                  width = -width;
                  left2 -= width;
                } else if (height < 0) {
                  action = ACTION_NORTH_WEST;
                  height = -height;
                  top2 -= height;
                }
                break;
              case ACTION_SOUTH_EAST:
                if (aspectRatio) {
                  if (range.x >= 0 && (right2 >= maxWidth || bottom2 >= maxHeight)) {
                    renderable = false;
                    break;
                  }
                  check(ACTION_EAST);
                  width += range.x;
                  height = width / aspectRatio;
                } else {
                  check(ACTION_SOUTH);
                  check(ACTION_EAST);
                  if (range.x >= 0) {
                    if (right2 < maxWidth) {
                      width += range.x;
                    } else if (range.y >= 0 && bottom2 >= maxHeight) {
                      renderable = false;
                    }
                  } else {
                    width += range.x;
                  }
                  if (range.y >= 0) {
                    if (bottom2 < maxHeight) {
                      height += range.y;
                    }
                  } else {
                    height += range.y;
                  }
                }
                if (width < 0 && height < 0) {
                  action = ACTION_NORTH_WEST;
                  height = -height;
                  width = -width;
                  top2 -= height;
                  left2 -= width;
                } else if (width < 0) {
                  action = ACTION_SOUTH_WEST;
                  width = -width;
                  left2 -= width;
                } else if (height < 0) {
                  action = ACTION_NORTH_EAST;
                  height = -height;
                  top2 -= height;
                }
                break;
              case ACTION_MOVE:
                this.move(range.x, range.y);
                renderable = false;
                break;
              case ACTION_ZOOM:
                this.zoom(getMaxZoomRatio(pointers), event);
                renderable = false;
                break;
              case ACTION_CROP:
                if (!range.x || !range.y) {
                  renderable = false;
                  break;
                }
                offset2 = getOffset(this.cropper);
                left2 = pointer.startX - offset2.left;
                top2 = pointer.startY - offset2.top;
                width = cropBoxData.minWidth;
                height = cropBoxData.minHeight;
                if (range.x > 0) {
                  action = range.y > 0 ? ACTION_SOUTH_EAST : ACTION_NORTH_EAST;
                } else if (range.x < 0) {
                  left2 -= width;
                  action = range.y > 0 ? ACTION_SOUTH_WEST : ACTION_NORTH_WEST;
                }
                if (range.y < 0) {
                  top2 -= height;
                }
                if (!this.cropped) {
                  removeClass(this.cropBox, CLASS_HIDDEN);
                  this.cropped = true;
                  if (this.limited) {
                    this.limitCropBox(true, true);
                  }
                }
                break;
            }
            if (renderable) {
              cropBoxData.width = width;
              cropBoxData.height = height;
              cropBoxData.left = left2;
              cropBoxData.top = top2;
              this.action = action;
              this.renderCropBox();
            }
            forEach(pointers, function(p2) {
              p2.startX = p2.endX;
              p2.startY = p2.endY;
            });
          }
        };
        var methods = {
          crop: function crop() {
            if (this.ready && !this.cropped && !this.disabled) {
              this.cropped = true;
              this.limitCropBox(true, true);
              if (this.options.modal) {
                addClass(this.dragBox, CLASS_MODAL);
              }
              removeClass(this.cropBox, CLASS_HIDDEN);
              this.setCropBoxData(this.initialCropBoxData);
            }
            return this;
          },
          reset: function reset() {
            if (this.ready && !this.disabled) {
              this.imageData = assign({}, this.initialImageData);
              this.canvasData = assign({}, this.initialCanvasData);
              this.cropBoxData = assign({}, this.initialCropBoxData);
              this.renderCanvas();
              if (this.cropped) {
                this.renderCropBox();
              }
            }
            return this;
          },
          clear: function clear2() {
            if (this.cropped && !this.disabled) {
              assign(this.cropBoxData, {
                left: 0,
                top: 0,
                width: 0,
                height: 0
              });
              this.cropped = false;
              this.renderCropBox();
              this.limitCanvas(true, true);
              this.renderCanvas();
              removeClass(this.dragBox, CLASS_MODAL);
              addClass(this.cropBox, CLASS_HIDDEN);
            }
            return this;
          },
          replace: function replace(url) {
            var hasSameSize = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : false;
            if (!this.disabled && url) {
              if (this.isImg) {
                this.element.src = url;
              }
              if (hasSameSize) {
                this.url = url;
                this.image.src = url;
                if (this.ready) {
                  this.viewBoxImage.src = url;
                  forEach(this.previews, function(element) {
                    element.getElementsByTagName("img")[0].src = url;
                  });
                }
              } else {
                if (this.isImg) {
                  this.replaced = true;
                }
                this.options.data = null;
                this.uncreate();
                this.load(url);
              }
            }
            return this;
          },
          enable: function enable() {
            if (this.ready && this.disabled) {
              this.disabled = false;
              removeClass(this.cropper, CLASS_DISABLED);
            }
            return this;
          },
          disable: function disable() {
            if (this.ready && !this.disabled) {
              this.disabled = true;
              addClass(this.cropper, CLASS_DISABLED);
            }
            return this;
          },
          destroy: function destroy() {
            var element = this.element;
            if (!element[NAMESPACE]) {
              return this;
            }
            element[NAMESPACE] = void 0;
            if (this.isImg && this.replaced) {
              element.src = this.originalUrl;
            }
            this.uncreate();
            return this;
          },
          move: function move(offsetX) {
            var offsetY = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : offsetX;
            var _this$canvasData = this.canvasData, left2 = _this$canvasData.left, top2 = _this$canvasData.top;
            return this.moveTo(isUndefined(offsetX) ? offsetX : left2 + Number(offsetX), isUndefined(offsetY) ? offsetY : top2 + Number(offsetY));
          },
          moveTo: function moveTo(x) {
            var y = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : x;
            var canvasData = this.canvasData;
            var changed = false;
            x = Number(x);
            y = Number(y);
            if (this.ready && !this.disabled && this.options.movable) {
              if (isNumber(x)) {
                canvasData.left = x;
                changed = true;
              }
              if (isNumber(y)) {
                canvasData.top = y;
                changed = true;
              }
              if (changed) {
                this.renderCanvas(true);
              }
            }
            return this;
          },
          zoom: function zoom(ratio, _originalEvent) {
            var canvasData = this.canvasData;
            ratio = Number(ratio);
            if (ratio < 0) {
              ratio = 1 / (1 - ratio);
            } else {
              ratio = 1 + ratio;
            }
            return this.zoomTo(canvasData.width * ratio / canvasData.naturalWidth, null, _originalEvent);
          },
          zoomTo: function zoomTo(ratio, pivot, _originalEvent) {
            var options = this.options, canvasData = this.canvasData;
            var width = canvasData.width, height = canvasData.height, naturalWidth = canvasData.naturalWidth, naturalHeight = canvasData.naturalHeight;
            ratio = Number(ratio);
            if (ratio >= 0 && this.ready && !this.disabled && options.zoomable) {
              var newWidth = naturalWidth * ratio;
              var newHeight = naturalHeight * ratio;
              if (dispatchEvent(this.element, EVENT_ZOOM, {
                ratio,
                oldRatio: width / naturalWidth,
                originalEvent: _originalEvent
              }) === false) {
                return this;
              }
              if (_originalEvent) {
                var pointers = this.pointers;
                var offset2 = getOffset(this.cropper);
                var center = pointers && Object.keys(pointers).length ? getPointersCenter(pointers) : {
                  pageX: _originalEvent.pageX,
                  pageY: _originalEvent.pageY
                };
                canvasData.left -= (newWidth - width) * ((center.pageX - offset2.left - canvasData.left) / width);
                canvasData.top -= (newHeight - height) * ((center.pageY - offset2.top - canvasData.top) / height);
              } else if (isPlainObject3(pivot) && isNumber(pivot.x) && isNumber(pivot.y)) {
                canvasData.left -= (newWidth - width) * ((pivot.x - canvasData.left) / width);
                canvasData.top -= (newHeight - height) * ((pivot.y - canvasData.top) / height);
              } else {
                canvasData.left -= (newWidth - width) / 2;
                canvasData.top -= (newHeight - height) / 2;
              }
              canvasData.width = newWidth;
              canvasData.height = newHeight;
              this.renderCanvas(true);
            }
            return this;
          },
          rotate: function rotate(degree) {
            return this.rotateTo((this.imageData.rotate || 0) + Number(degree));
          },
          rotateTo: function rotateTo(degree) {
            degree = Number(degree);
            if (isNumber(degree) && this.ready && !this.disabled && this.options.rotatable) {
              this.imageData.rotate = degree % 360;
              this.renderCanvas(true, true);
            }
            return this;
          },
          scaleX: function scaleX(_scaleX) {
            var scaleY = this.imageData.scaleY;
            return this.scale(_scaleX, isNumber(scaleY) ? scaleY : 1);
          },
          scaleY: function scaleY(_scaleY) {
            var scaleX = this.imageData.scaleX;
            return this.scale(isNumber(scaleX) ? scaleX : 1, _scaleY);
          },
          scale: function scale(scaleX) {
            var scaleY = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : scaleX;
            var imageData = this.imageData;
            var transformed = false;
            scaleX = Number(scaleX);
            scaleY = Number(scaleY);
            if (this.ready && !this.disabled && this.options.scalable) {
              if (isNumber(scaleX)) {
                imageData.scaleX = scaleX;
                transformed = true;
              }
              if (isNumber(scaleY)) {
                imageData.scaleY = scaleY;
                transformed = true;
              }
              if (transformed) {
                this.renderCanvas(true, true);
              }
            }
            return this;
          },
          getData: function getData2() {
            var rounded = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : false;
            var options = this.options, imageData = this.imageData, canvasData = this.canvasData, cropBoxData = this.cropBoxData;
            var data;
            if (this.ready && this.cropped) {
              data = {
                x: cropBoxData.left - canvasData.left,
                y: cropBoxData.top - canvasData.top,
                width: cropBoxData.width,
                height: cropBoxData.height
              };
              var ratio = imageData.width / imageData.naturalWidth;
              forEach(data, function(n, i) {
                data[i] = n / ratio;
              });
              if (rounded) {
                var bottom2 = Math.round(data.y + data.height);
                var right2 = Math.round(data.x + data.width);
                data.x = Math.round(data.x);
                data.y = Math.round(data.y);
                data.width = right2 - data.x;
                data.height = bottom2 - data.y;
              }
            } else {
              data = {
                x: 0,
                y: 0,
                width: 0,
                height: 0
              };
            }
            if (options.rotatable) {
              data.rotate = imageData.rotate || 0;
            }
            if (options.scalable) {
              data.scaleX = imageData.scaleX || 1;
              data.scaleY = imageData.scaleY || 1;
            }
            return data;
          },
          setData: function setData2(data) {
            var options = this.options, imageData = this.imageData, canvasData = this.canvasData;
            var cropBoxData = {};
            if (this.ready && !this.disabled && isPlainObject3(data)) {
              var transformed = false;
              if (options.rotatable) {
                if (isNumber(data.rotate) && data.rotate !== imageData.rotate) {
                  imageData.rotate = data.rotate;
                  transformed = true;
                }
              }
              if (options.scalable) {
                if (isNumber(data.scaleX) && data.scaleX !== imageData.scaleX) {
                  imageData.scaleX = data.scaleX;
                  transformed = true;
                }
                if (isNumber(data.scaleY) && data.scaleY !== imageData.scaleY) {
                  imageData.scaleY = data.scaleY;
                  transformed = true;
                }
              }
              if (transformed) {
                this.renderCanvas(true, true);
              }
              var ratio = imageData.width / imageData.naturalWidth;
              if (isNumber(data.x)) {
                cropBoxData.left = data.x * ratio + canvasData.left;
              }
              if (isNumber(data.y)) {
                cropBoxData.top = data.y * ratio + canvasData.top;
              }
              if (isNumber(data.width)) {
                cropBoxData.width = data.width * ratio;
              }
              if (isNumber(data.height)) {
                cropBoxData.height = data.height * ratio;
              }
              this.setCropBoxData(cropBoxData);
            }
            return this;
          },
          getContainerData: function getContainerData() {
            return this.ready ? assign({}, this.containerData) : {};
          },
          getImageData: function getImageData() {
            return this.sized ? assign({}, this.imageData) : {};
          },
          getCanvasData: function getCanvasData() {
            var canvasData = this.canvasData;
            var data = {};
            if (this.ready) {
              forEach(["left", "top", "width", "height", "naturalWidth", "naturalHeight"], function(n) {
                data[n] = canvasData[n];
              });
            }
            return data;
          },
          setCanvasData: function setCanvasData(data) {
            var canvasData = this.canvasData;
            var aspectRatio = canvasData.aspectRatio;
            if (this.ready && !this.disabled && isPlainObject3(data)) {
              if (isNumber(data.left)) {
                canvasData.left = data.left;
              }
              if (isNumber(data.top)) {
                canvasData.top = data.top;
              }
              if (isNumber(data.width)) {
                canvasData.width = data.width;
                canvasData.height = data.width / aspectRatio;
              } else if (isNumber(data.height)) {
                canvasData.height = data.height;
                canvasData.width = data.height * aspectRatio;
              }
              this.renderCanvas(true);
            }
            return this;
          },
          getCropBoxData: function getCropBoxData() {
            var cropBoxData = this.cropBoxData;
            var data;
            if (this.ready && this.cropped) {
              data = {
                left: cropBoxData.left,
                top: cropBoxData.top,
                width: cropBoxData.width,
                height: cropBoxData.height
              };
            }
            return data || {};
          },
          setCropBoxData: function setCropBoxData(data) {
            var cropBoxData = this.cropBoxData;
            var aspectRatio = this.options.aspectRatio;
            var widthChanged;
            var heightChanged;
            if (this.ready && this.cropped && !this.disabled && isPlainObject3(data)) {
              if (isNumber(data.left)) {
                cropBoxData.left = data.left;
              }
              if (isNumber(data.top)) {
                cropBoxData.top = data.top;
              }
              if (isNumber(data.width) && data.width !== cropBoxData.width) {
                widthChanged = true;
                cropBoxData.width = data.width;
              }
              if (isNumber(data.height) && data.height !== cropBoxData.height) {
                heightChanged = true;
                cropBoxData.height = data.height;
              }
              if (aspectRatio) {
                if (widthChanged) {
                  cropBoxData.height = cropBoxData.width / aspectRatio;
                } else if (heightChanged) {
                  cropBoxData.width = cropBoxData.height * aspectRatio;
                }
              }
              this.renderCropBox();
            }
            return this;
          },
          getCroppedCanvas: function getCroppedCanvas() {
            var options = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : {};
            if (!this.ready || !window.HTMLCanvasElement) {
              return null;
            }
            var canvasData = this.canvasData;
            var source = getSourceCanvas(this.image, this.imageData, canvasData, options);
            if (!this.cropped) {
              return source;
            }
            var _this$getData = this.getData(options.rounded), initialX = _this$getData.x, initialY = _this$getData.y, initialWidth = _this$getData.width, initialHeight = _this$getData.height;
            var ratio = source.width / Math.floor(canvasData.naturalWidth);
            if (ratio !== 1) {
              initialX *= ratio;
              initialY *= ratio;
              initialWidth *= ratio;
              initialHeight *= ratio;
            }
            var aspectRatio = initialWidth / initialHeight;
            var maxSizes = getAdjustedSizes({
              aspectRatio,
              width: options.maxWidth || Infinity,
              height: options.maxHeight || Infinity
            });
            var minSizes = getAdjustedSizes({
              aspectRatio,
              width: options.minWidth || 0,
              height: options.minHeight || 0
            }, "cover");
            var _getAdjustedSizes = getAdjustedSizes({
              aspectRatio,
              width: options.width || (ratio !== 1 ? source.width : initialWidth),
              height: options.height || (ratio !== 1 ? source.height : initialHeight)
            }), width = _getAdjustedSizes.width, height = _getAdjustedSizes.height;
            width = Math.min(maxSizes.width, Math.max(minSizes.width, width));
            height = Math.min(maxSizes.height, Math.max(minSizes.height, height));
            var canvas = document.createElement("canvas");
            var context = canvas.getContext("2d");
            canvas.width = normalizeDecimalNumber(width);
            canvas.height = normalizeDecimalNumber(height);
            context.fillStyle = options.fillColor || "transparent";
            context.fillRect(0, 0, width, height);
            var _options$imageSmoothi = options.imageSmoothingEnabled, imageSmoothingEnabled = _options$imageSmoothi === void 0 ? true : _options$imageSmoothi, imageSmoothingQuality = options.imageSmoothingQuality;
            context.imageSmoothingEnabled = imageSmoothingEnabled;
            if (imageSmoothingQuality) {
              context.imageSmoothingQuality = imageSmoothingQuality;
            }
            var sourceWidth = source.width;
            var sourceHeight = source.height;
            var srcX = initialX;
            var srcY = initialY;
            var srcWidth;
            var srcHeight;
            var dstX;
            var dstY;
            var dstWidth;
            var dstHeight;
            if (srcX <= -initialWidth || srcX > sourceWidth) {
              srcX = 0;
              srcWidth = 0;
              dstX = 0;
              dstWidth = 0;
            } else if (srcX <= 0) {
              dstX = -srcX;
              srcX = 0;
              srcWidth = Math.min(sourceWidth, initialWidth + srcX);
              dstWidth = srcWidth;
            } else if (srcX <= sourceWidth) {
              dstX = 0;
              srcWidth = Math.min(initialWidth, sourceWidth - srcX);
              dstWidth = srcWidth;
            }
            if (srcWidth <= 0 || srcY <= -initialHeight || srcY > sourceHeight) {
              srcY = 0;
              srcHeight = 0;
              dstY = 0;
              dstHeight = 0;
            } else if (srcY <= 0) {
              dstY = -srcY;
              srcY = 0;
              srcHeight = Math.min(sourceHeight, initialHeight + srcY);
              dstHeight = srcHeight;
            } else if (srcY <= sourceHeight) {
              dstY = 0;
              srcHeight = Math.min(initialHeight, sourceHeight - srcY);
              dstHeight = srcHeight;
            }
            var params = [srcX, srcY, srcWidth, srcHeight];
            if (dstWidth > 0 && dstHeight > 0) {
              var scale = width / initialWidth;
              params.push(dstX * scale, dstY * scale, dstWidth * scale, dstHeight * scale);
            }
            context.drawImage.apply(context, [source].concat(_toConsumableArray(params.map(function(param) {
              return Math.floor(normalizeDecimalNumber(param));
            }))));
            return canvas;
          },
          setAspectRatio: function setAspectRatio(aspectRatio) {
            var options = this.options;
            if (!this.disabled && !isUndefined(aspectRatio)) {
              options.aspectRatio = Math.max(0, aspectRatio) || NaN;
              if (this.ready) {
                this.initCropBox();
                if (this.cropped) {
                  this.renderCropBox();
                }
              }
            }
            return this;
          },
          setDragMode: function setDragMode(mode) {
            var options = this.options, dragBox = this.dragBox, face = this.face;
            if (this.ready && !this.disabled) {
              var croppable = mode === DRAG_MODE_CROP;
              var movable = options.movable && mode === DRAG_MODE_MOVE;
              mode = croppable || movable ? mode : DRAG_MODE_NONE;
              options.dragMode = mode;
              setData(dragBox, DATA_ACTION, mode);
              toggleClass(dragBox, CLASS_CROP, croppable);
              toggleClass(dragBox, CLASS_MOVE, movable);
              if (!options.cropBoxMovable) {
                setData(face, DATA_ACTION, mode);
                toggleClass(face, CLASS_CROP, croppable);
                toggleClass(face, CLASS_MOVE, movable);
              }
            }
            return this;
          }
        };
        var AnotherCropper = WINDOW.Cropper;
        var Cropper2 = /* @__PURE__ */ function() {
          function Cropper3(element) {
            var options = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : {};
            _classCallCheck(this, Cropper3);
            if (!element || !REGEXP_TAG_NAME.test(element.tagName)) {
              throw new Error("The first argument is required and must be an <img> or <canvas> element.");
            }
            this.element = element;
            this.options = assign({}, DEFAULTS, isPlainObject3(options) && options);
            this.cropped = false;
            this.disabled = false;
            this.pointers = {};
            this.ready = false;
            this.reloading = false;
            this.replaced = false;
            this.sized = false;
            this.sizing = false;
            this.init();
          }
          _createClass(Cropper3, [{
            key: "init",
            value: function init() {
              var element = this.element;
              var tagName = element.tagName.toLowerCase();
              var url;
              if (element[NAMESPACE]) {
                return;
              }
              element[NAMESPACE] = this;
              if (tagName === "img") {
                this.isImg = true;
                url = element.getAttribute("src") || "";
                this.originalUrl = url;
                if (!url) {
                  return;
                }
                url = element.src;
              } else if (tagName === "canvas" && window.HTMLCanvasElement) {
                url = element.toDataURL();
              }
              this.load(url);
            }
          }, {
            key: "load",
            value: function load(url) {
              var _this = this;
              if (!url) {
                return;
              }
              this.url = url;
              this.imageData = {};
              var element = this.element, options = this.options;
              if (!options.rotatable && !options.scalable) {
                options.checkOrientation = false;
              }
              if (!options.checkOrientation || !window.ArrayBuffer) {
                this.clone();
                return;
              }
              if (REGEXP_DATA_URL.test(url)) {
                if (REGEXP_DATA_URL_JPEG.test(url)) {
                  this.read(dataURLToArrayBuffer(url));
                } else {
                  this.clone();
                }
                return;
              }
              var xhr = new XMLHttpRequest();
              var clone = this.clone.bind(this);
              this.reloading = true;
              this.xhr = xhr;
              xhr.onabort = clone;
              xhr.onerror = clone;
              xhr.ontimeout = clone;
              xhr.onprogress = function() {
                if (xhr.getResponseHeader("content-type") !== MIME_TYPE_JPEG) {
                  xhr.abort();
                }
              };
              xhr.onload = function() {
                _this.read(xhr.response);
              };
              xhr.onloadend = function() {
                _this.reloading = false;
                _this.xhr = null;
              };
              if (options.checkCrossOrigin && isCrossOriginURL(url) && element.crossOrigin) {
                url = addTimestamp(url);
              }
              xhr.open("GET", url, true);
              xhr.responseType = "arraybuffer";
              xhr.withCredentials = element.crossOrigin === "use-credentials";
              xhr.send();
            }
          }, {
            key: "read",
            value: function read2(arrayBuffer) {
              var options = this.options, imageData = this.imageData;
              var orientation = resetAndGetOrientation(arrayBuffer);
              var rotate = 0;
              var scaleX = 1;
              var scaleY = 1;
              if (orientation > 1) {
                this.url = arrayBufferToDataURL(arrayBuffer, MIME_TYPE_JPEG);
                var _parseOrientation = parseOrientation(orientation);
                rotate = _parseOrientation.rotate;
                scaleX = _parseOrientation.scaleX;
                scaleY = _parseOrientation.scaleY;
              }
              if (options.rotatable) {
                imageData.rotate = rotate;
              }
              if (options.scalable) {
                imageData.scaleX = scaleX;
                imageData.scaleY = scaleY;
              }
              this.clone();
            }
          }, {
            key: "clone",
            value: function clone() {
              var element = this.element, url = this.url;
              var crossOrigin = element.crossOrigin;
              var crossOriginUrl = url;
              if (this.options.checkCrossOrigin && isCrossOriginURL(url)) {
                if (!crossOrigin) {
                  crossOrigin = "anonymous";
                }
                crossOriginUrl = addTimestamp(url);
              }
              this.crossOrigin = crossOrigin;
              this.crossOriginUrl = crossOriginUrl;
              var image = document.createElement("img");
              if (crossOrigin) {
                image.crossOrigin = crossOrigin;
              }
              image.src = crossOriginUrl || url;
              image.alt = element.alt || "The image to crop";
              this.image = image;
              image.onload = this.start.bind(this);
              image.onerror = this.stop.bind(this);
              addClass(image, CLASS_HIDE);
              element.parentNode.insertBefore(image, element.nextSibling);
            }
          }, {
            key: "start",
            value: function start2() {
              var _this2 = this;
              var image = this.image;
              image.onload = null;
              image.onerror = null;
              this.sizing = true;
              var isIOSWebKit = WINDOW.navigator && /(?:iPad|iPhone|iPod).*?AppleWebKit/i.test(WINDOW.navigator.userAgent);
              var done = function done2(naturalWidth, naturalHeight) {
                assign(_this2.imageData, {
                  naturalWidth,
                  naturalHeight,
                  aspectRatio: naturalWidth / naturalHeight
                });
                _this2.initialImageData = assign({}, _this2.imageData);
                _this2.sizing = false;
                _this2.sized = true;
                _this2.build();
              };
              if (image.naturalWidth && !isIOSWebKit) {
                done(image.naturalWidth, image.naturalHeight);
                return;
              }
              var sizingImage = document.createElement("img");
              var body = document.body || document.documentElement;
              this.sizingImage = sizingImage;
              sizingImage.onload = function() {
                done(sizingImage.width, sizingImage.height);
                if (!isIOSWebKit) {
                  body.removeChild(sizingImage);
                }
              };
              sizingImage.src = image.src;
              if (!isIOSWebKit) {
                sizingImage.style.cssText = "left:0;max-height:none!important;max-width:none!important;min-height:0!important;min-width:0!important;opacity:0;position:absolute;top:0;z-index:-1;";
                body.appendChild(sizingImage);
              }
            }
          }, {
            key: "stop",
            value: function stop3() {
              var image = this.image;
              image.onload = null;
              image.onerror = null;
              image.parentNode.removeChild(image);
              this.image = null;
            }
          }, {
            key: "build",
            value: function build() {
              if (!this.sized || this.ready) {
                return;
              }
              var element = this.element, options = this.options, image = this.image;
              var container = element.parentNode;
              var template = document.createElement("div");
              template.innerHTML = TEMPLATE;
              var cropper = template.querySelector(".".concat(NAMESPACE, "-container"));
              var canvas = cropper.querySelector(".".concat(NAMESPACE, "-canvas"));
              var dragBox = cropper.querySelector(".".concat(NAMESPACE, "-drag-box"));
              var cropBox = cropper.querySelector(".".concat(NAMESPACE, "-crop-box"));
              var face = cropBox.querySelector(".".concat(NAMESPACE, "-face"));
              this.container = container;
              this.cropper = cropper;
              this.canvas = canvas;
              this.dragBox = dragBox;
              this.cropBox = cropBox;
              this.viewBox = cropper.querySelector(".".concat(NAMESPACE, "-view-box"));
              this.face = face;
              canvas.appendChild(image);
              addClass(element, CLASS_HIDDEN);
              container.insertBefore(cropper, element.nextSibling);
              removeClass(image, CLASS_HIDE);
              this.initPreview();
              this.bind();
              options.initialAspectRatio = Math.max(0, options.initialAspectRatio) || NaN;
              options.aspectRatio = Math.max(0, options.aspectRatio) || NaN;
              options.viewMode = Math.max(0, Math.min(3, Math.round(options.viewMode))) || 0;
              addClass(cropBox, CLASS_HIDDEN);
              if (!options.guides) {
                addClass(cropBox.getElementsByClassName("".concat(NAMESPACE, "-dashed")), CLASS_HIDDEN);
              }
              if (!options.center) {
                addClass(cropBox.getElementsByClassName("".concat(NAMESPACE, "-center")), CLASS_HIDDEN);
              }
              if (options.background) {
                addClass(cropper, "".concat(NAMESPACE, "-bg"));
              }
              if (!options.highlight) {
                addClass(face, CLASS_INVISIBLE);
              }
              if (options.cropBoxMovable) {
                addClass(face, CLASS_MOVE);
                setData(face, DATA_ACTION, ACTION_ALL);
              }
              if (!options.cropBoxResizable) {
                addClass(cropBox.getElementsByClassName("".concat(NAMESPACE, "-line")), CLASS_HIDDEN);
                addClass(cropBox.getElementsByClassName("".concat(NAMESPACE, "-point")), CLASS_HIDDEN);
              }
              this.render();
              this.ready = true;
              this.setDragMode(options.dragMode);
              if (options.autoCrop) {
                this.crop();
              }
              this.setData(options.data);
              if (isFunction3(options.ready)) {
                addListener(element, EVENT_READY, options.ready, {
                  once: true
                });
              }
              dispatchEvent(element, EVENT_READY);
            }
          }, {
            key: "unbuild",
            value: function unbuild() {
              if (!this.ready) {
                return;
              }
              this.ready = false;
              this.unbind();
              this.resetPreview();
              var parentNode = this.cropper.parentNode;
              if (parentNode) {
                parentNode.removeChild(this.cropper);
              }
              removeClass(this.element, CLASS_HIDDEN);
            }
          }, {
            key: "uncreate",
            value: function uncreate() {
              if (this.ready) {
                this.unbuild();
                this.ready = false;
                this.cropped = false;
              } else if (this.sizing) {
                this.sizingImage.onload = null;
                this.sizing = false;
                this.sized = false;
              } else if (this.reloading) {
                this.xhr.onabort = null;
                this.xhr.abort();
              } else if (this.image) {
                this.stop();
              }
            }
          }], [{
            key: "noConflict",
            value: function noConflict() {
              window.Cropper = AnotherCropper;
              return Cropper3;
            }
          }, {
            key: "setDefaults",
            value: function setDefaults(options) {
              assign(DEFAULTS, isPlainObject3(options) && options);
            }
          }]);
          return Cropper3;
        }();
        assign(Cropper2.prototype, render8, preview, events, handlers, change, methods);
        return Cropper2;
      });
    }
  });

  // ../powerpro/powerpro/public/js/app.bundle.js
  var functions = __toESM(require_functions());
  var create_material_sku = __toESM(require_create_material_sku());

  // ../powerpro/node_modules/@vue/shared/dist/shared.esm-bundler.js
  function makeMap(str) {
    const map3 = /* @__PURE__ */ Object.create(null);
    for (const key of str.split(","))
      map3[key] = 1;
    return (val) => val in map3;
  }
  var EMPTY_OBJ = true ? Object.freeze({}) : {};
  var EMPTY_ARR = true ? Object.freeze([]) : [];
  var NOOP = () => {
  };
  var NO = () => false;
  var isOn = (key) => key.charCodeAt(0) === 111 && key.charCodeAt(1) === 110 && (key.charCodeAt(2) > 122 || key.charCodeAt(2) < 97);
  var isModelListener = (key) => key.startsWith("onUpdate:");
  var extend = Object.assign;
  var remove = (arr, el) => {
    const i = arr.indexOf(el);
    if (i > -1) {
      arr.splice(i, 1);
    }
  };
  var hasOwnProperty = Object.prototype.hasOwnProperty;
  var hasOwn = (val, key) => hasOwnProperty.call(val, key);
  var isArray = Array.isArray;
  var isMap = (val) => toTypeString(val) === "[object Map]";
  var isSet = (val) => toTypeString(val) === "[object Set]";
  var isFunction = (val) => typeof val === "function";
  var isString = (val) => typeof val === "string";
  var isSymbol = (val) => typeof val === "symbol";
  var isObject = (val) => val !== null && typeof val === "object";
  var isPromise = (val) => {
    return (isObject(val) || isFunction(val)) && isFunction(val.then) && isFunction(val.catch);
  };
  var objectToString = Object.prototype.toString;
  var toTypeString = (value) => objectToString.call(value);
  var toRawType = (value) => {
    return toTypeString(value).slice(8, -1);
  };
  var isPlainObject = (val) => toTypeString(val) === "[object Object]";
  var isIntegerKey = (key) => isString(key) && key !== "NaN" && key[0] !== "-" && "" + parseInt(key, 10) === key;
  var isReservedProp = /* @__PURE__ */ makeMap(
    ",key,ref,ref_for,ref_key,onVnodeBeforeMount,onVnodeMounted,onVnodeBeforeUpdate,onVnodeUpdated,onVnodeBeforeUnmount,onVnodeUnmounted"
  );
  var isBuiltInDirective = /* @__PURE__ */ makeMap(
    "bind,cloak,else-if,else,for,html,if,model,on,once,pre,show,slot,text,memo"
  );
  var cacheStringFunction = (fn2) => {
    const cache = /* @__PURE__ */ Object.create(null);
    return (str) => {
      const hit = cache[str];
      return hit || (cache[str] = fn2(str));
    };
  };
  var camelizeRE = /-(\w)/g;
  var camelize = cacheStringFunction(
    (str) => {
      return str.replace(camelizeRE, (_, c) => c ? c.toUpperCase() : "");
    }
  );
  var hyphenateRE = /\B([A-Z])/g;
  var hyphenate = cacheStringFunction(
    (str) => str.replace(hyphenateRE, "-$1").toLowerCase()
  );
  var capitalize = cacheStringFunction((str) => {
    return str.charAt(0).toUpperCase() + str.slice(1);
  });
  var toHandlerKey = cacheStringFunction(
    (str) => {
      const s = str ? `on${capitalize(str)}` : ``;
      return s;
    }
  );
  var hasChanged = (value, oldValue) => !Object.is(value, oldValue);
  var invokeArrayFns = (fns, ...arg) => {
    for (let i = 0; i < fns.length; i++) {
      fns[i](...arg);
    }
  };
  var def = (obj, key, value, writable = false) => {
    Object.defineProperty(obj, key, {
      configurable: true,
      enumerable: false,
      writable,
      value
    });
  };
  var looseToNumber = (val) => {
    const n = parseFloat(val);
    return isNaN(n) ? val : n;
  };
  var _globalThis;
  var getGlobalThis = () => {
    return _globalThis || (_globalThis = typeof globalThis !== "undefined" ? globalThis : typeof self !== "undefined" ? self : typeof window !== "undefined" ? window : typeof global !== "undefined" ? global : {});
  };
  function normalizeStyle(value) {
    if (isArray(value)) {
      const res = {};
      for (let i = 0; i < value.length; i++) {
        const item = value[i];
        const normalized = isString(item) ? parseStringStyle(item) : normalizeStyle(item);
        if (normalized) {
          for (const key in normalized) {
            res[key] = normalized[key];
          }
        }
      }
      return res;
    } else if (isString(value) || isObject(value)) {
      return value;
    }
  }
  var listDelimiterRE = /;(?![^(]*\))/g;
  var propertyDelimiterRE = /:([^]+)/;
  var styleCommentRE = /\/\*[^]*?\*\//g;
  function parseStringStyle(cssText) {
    const ret = {};
    cssText.replace(styleCommentRE, "").split(listDelimiterRE).forEach((item) => {
      if (item) {
        const tmp = item.split(propertyDelimiterRE);
        tmp.length > 1 && (ret[tmp[0].trim()] = tmp[1].trim());
      }
    });
    return ret;
  }
  function normalizeClass(value) {
    let res = "";
    if (isString(value)) {
      res = value;
    } else if (isArray(value)) {
      for (let i = 0; i < value.length; i++) {
        const normalized = normalizeClass(value[i]);
        if (normalized) {
          res += normalized + " ";
        }
      }
    } else if (isObject(value)) {
      for (const name in value) {
        if (value[name]) {
          res += name + " ";
        }
      }
    }
    return res.trim();
  }
  var HTML_TAGS = "html,body,base,head,link,meta,style,title,address,article,aside,footer,header,hgroup,h1,h2,h3,h4,h5,h6,nav,section,div,dd,dl,dt,figcaption,figure,picture,hr,img,li,main,ol,p,pre,ul,a,b,abbr,bdi,bdo,br,cite,code,data,dfn,em,i,kbd,mark,q,rp,rt,ruby,s,samp,small,span,strong,sub,sup,time,u,var,wbr,area,audio,map,track,video,embed,object,param,source,canvas,script,noscript,del,ins,caption,col,colgroup,table,thead,tbody,td,th,tr,button,datalist,fieldset,form,input,label,legend,meter,optgroup,option,output,progress,select,textarea,details,dialog,menu,summary,template,blockquote,iframe,tfoot";
  var SVG_TAGS = "svg,animate,animateMotion,animateTransform,circle,clipPath,color-profile,defs,desc,discard,ellipse,feBlend,feColorMatrix,feComponentTransfer,feComposite,feConvolveMatrix,feDiffuseLighting,feDisplacementMap,feDistantLight,feDropShadow,feFlood,feFuncA,feFuncB,feFuncG,feFuncR,feGaussianBlur,feImage,feMerge,feMergeNode,feMorphology,feOffset,fePointLight,feSpecularLighting,feSpotLight,feTile,feTurbulence,filter,foreignObject,g,hatch,hatchpath,image,line,linearGradient,marker,mask,mesh,meshgradient,meshpatch,meshrow,metadata,mpath,path,pattern,polygon,polyline,radialGradient,rect,set,solidcolor,stop,switch,symbol,text,textPath,title,tspan,unknown,use,view";
  var MATH_TAGS = "annotation,annotation-xml,maction,maligngroup,malignmark,math,menclose,merror,mfenced,mfrac,mfraction,mglyph,mi,mlabeledtr,mlongdiv,mmultiscripts,mn,mo,mover,mpadded,mphantom,mprescripts,mroot,mrow,ms,mscarries,mscarry,msgroup,msline,mspace,msqrt,msrow,mstack,mstyle,msub,msubsup,msup,mtable,mtd,mtext,mtr,munder,munderover,none,semantics";
  var isHTMLTag = /* @__PURE__ */ makeMap(HTML_TAGS);
  var isSVGTag = /* @__PURE__ */ makeMap(SVG_TAGS);
  var isMathMLTag = /* @__PURE__ */ makeMap(MATH_TAGS);
  var specialBooleanAttrs = `itemscope,allowfullscreen,formnovalidate,ismap,nomodule,novalidate,readonly`;
  var isSpecialBooleanAttr = /* @__PURE__ */ makeMap(specialBooleanAttrs);
  var isBooleanAttr = /* @__PURE__ */ makeMap(
    specialBooleanAttrs + `,async,autofocus,autoplay,controls,default,defer,disabled,hidden,inert,loop,open,required,reversed,scoped,seamless,checked,muted,multiple,selected`
  );
  function includeBooleanAttr(value) {
    return !!value || value === "";
  }
  var isRef = (val) => {
    return !!(val && val["__v_isRef"] === true);
  };
  var toDisplayString = (val) => {
    return isString(val) ? val : val == null ? "" : isArray(val) || isObject(val) && (val.toString === objectToString || !isFunction(val.toString)) ? isRef(val) ? toDisplayString(val.value) : JSON.stringify(val, replacer, 2) : String(val);
  };
  var replacer = (_key, val) => {
    if (isRef(val)) {
      return replacer(_key, val.value);
    } else if (isMap(val)) {
      return {
        [`Map(${val.size})`]: [...val.entries()].reduce(
          (entries, [key, val2], i) => {
            entries[stringifySymbol(key, i) + " =>"] = val2;
            return entries;
          },
          {}
        )
      };
    } else if (isSet(val)) {
      return {
        [`Set(${val.size})`]: [...val.values()].map((v) => stringifySymbol(v))
      };
    } else if (isSymbol(val)) {
      return stringifySymbol(val);
    } else if (isObject(val) && !isArray(val) && !isPlainObject(val)) {
      return String(val);
    }
    return val;
  };
  var stringifySymbol = (v, i = "") => {
    var _a;
    return isSymbol(v) ? `Symbol(${(_a = v.description) != null ? _a : i})` : v;
  };

  // ../powerpro/node_modules/@vue/reactivity/dist/reactivity.esm-bundler.js
  function warn(msg, ...args) {
    console.warn(`[Vue warn] ${msg}`, ...args);
  }
  var activeEffectScope;
  var EffectScope = class {
    constructor(detached = false) {
      this.detached = detached;
      this._active = true;
      this.effects = [];
      this.cleanups = [];
      this._isPaused = false;
      this.parent = activeEffectScope;
      if (!detached && activeEffectScope) {
        this.index = (activeEffectScope.scopes || (activeEffectScope.scopes = [])).push(
          this
        ) - 1;
      }
    }
    get active() {
      return this._active;
    }
    pause() {
      if (this._active) {
        this._isPaused = true;
        let i, l;
        if (this.scopes) {
          for (i = 0, l = this.scopes.length; i < l; i++) {
            this.scopes[i].pause();
          }
        }
        for (i = 0, l = this.effects.length; i < l; i++) {
          this.effects[i].pause();
        }
      }
    }
    resume() {
      if (this._active) {
        if (this._isPaused) {
          this._isPaused = false;
          let i, l;
          if (this.scopes) {
            for (i = 0, l = this.scopes.length; i < l; i++) {
              this.scopes[i].resume();
            }
          }
          for (i = 0, l = this.effects.length; i < l; i++) {
            this.effects[i].resume();
          }
        }
      }
    }
    run(fn2) {
      if (this._active) {
        const currentEffectScope = activeEffectScope;
        try {
          activeEffectScope = this;
          return fn2();
        } finally {
          activeEffectScope = currentEffectScope;
        }
      } else if (true) {
        warn(`cannot run an inactive effect scope.`);
      }
    }
    on() {
      activeEffectScope = this;
    }
    off() {
      activeEffectScope = this.parent;
    }
    stop(fromParent) {
      if (this._active) {
        let i, l;
        for (i = 0, l = this.effects.length; i < l; i++) {
          this.effects[i].stop();
        }
        for (i = 0, l = this.cleanups.length; i < l; i++) {
          this.cleanups[i]();
        }
        if (this.scopes) {
          for (i = 0, l = this.scopes.length; i < l; i++) {
            this.scopes[i].stop(true);
          }
        }
        if (!this.detached && this.parent && !fromParent) {
          const last = this.parent.scopes.pop();
          if (last && last !== this) {
            this.parent.scopes[this.index] = last;
            last.index = this.index;
          }
        }
        this.parent = void 0;
        this._active = false;
      }
    }
  };
  function getCurrentScope() {
    return activeEffectScope;
  }
  var activeSub;
  var pausedQueueEffects = /* @__PURE__ */ new WeakSet();
  var ReactiveEffect = class {
    constructor(fn2) {
      this.fn = fn2;
      this.deps = void 0;
      this.depsTail = void 0;
      this.flags = 1 | 4;
      this.next = void 0;
      this.cleanup = void 0;
      this.scheduler = void 0;
      if (activeEffectScope && activeEffectScope.active) {
        activeEffectScope.effects.push(this);
      }
    }
    pause() {
      this.flags |= 64;
    }
    resume() {
      if (this.flags & 64) {
        this.flags &= ~64;
        if (pausedQueueEffects.has(this)) {
          pausedQueueEffects.delete(this);
          this.trigger();
        }
      }
    }
    notify() {
      if (this.flags & 2 && !(this.flags & 32)) {
        return;
      }
      if (!(this.flags & 8)) {
        batch(this);
      }
    }
    run() {
      if (!(this.flags & 1)) {
        return this.fn();
      }
      this.flags |= 2;
      cleanupEffect(this);
      prepareDeps(this);
      const prevEffect = activeSub;
      const prevShouldTrack = shouldTrack;
      activeSub = this;
      shouldTrack = true;
      try {
        return this.fn();
      } finally {
        if (activeSub !== this) {
          warn(
            "Active effect was not restored correctly - this is likely a Vue internal bug."
          );
        }
        cleanupDeps(this);
        activeSub = prevEffect;
        shouldTrack = prevShouldTrack;
        this.flags &= ~2;
      }
    }
    stop() {
      if (this.flags & 1) {
        for (let link = this.deps; link; link = link.nextDep) {
          removeSub(link);
        }
        this.deps = this.depsTail = void 0;
        cleanupEffect(this);
        this.onStop && this.onStop();
        this.flags &= ~1;
      }
    }
    trigger() {
      if (this.flags & 64) {
        pausedQueueEffects.add(this);
      } else if (this.scheduler) {
        this.scheduler();
      } else {
        this.runIfDirty();
      }
    }
    runIfDirty() {
      if (isDirty(this)) {
        this.run();
      }
    }
    get dirty() {
      return isDirty(this);
    }
  };
  var batchDepth = 0;
  var batchedSub;
  var batchedComputed;
  function batch(sub, isComputed = false) {
    sub.flags |= 8;
    if (isComputed) {
      sub.next = batchedComputed;
      batchedComputed = sub;
      return;
    }
    sub.next = batchedSub;
    batchedSub = sub;
  }
  function startBatch() {
    batchDepth++;
  }
  function endBatch() {
    if (--batchDepth > 0) {
      return;
    }
    if (batchedComputed) {
      let e = batchedComputed;
      batchedComputed = void 0;
      while (e) {
        const next = e.next;
        e.next = void 0;
        e.flags &= ~8;
        e = next;
      }
    }
    let error;
    while (batchedSub) {
      let e = batchedSub;
      batchedSub = void 0;
      while (e) {
        const next = e.next;
        e.next = void 0;
        e.flags &= ~8;
        if (e.flags & 1) {
          try {
            ;
            e.trigger();
          } catch (err) {
            if (!error)
              error = err;
          }
        }
        e = next;
      }
    }
    if (error)
      throw error;
  }
  function prepareDeps(sub) {
    for (let link = sub.deps; link; link = link.nextDep) {
      link.version = -1;
      link.prevActiveLink = link.dep.activeLink;
      link.dep.activeLink = link;
    }
  }
  function cleanupDeps(sub) {
    let head;
    let tail = sub.depsTail;
    let link = tail;
    while (link) {
      const prev = link.prevDep;
      if (link.version === -1) {
        if (link === tail)
          tail = prev;
        removeSub(link);
        removeDep(link);
      } else {
        head = link;
      }
      link.dep.activeLink = link.prevActiveLink;
      link.prevActiveLink = void 0;
      link = prev;
    }
    sub.deps = head;
    sub.depsTail = tail;
  }
  function isDirty(sub) {
    for (let link = sub.deps; link; link = link.nextDep) {
      if (link.dep.version !== link.version || link.dep.computed && (refreshComputed(link.dep.computed) || link.dep.version !== link.version)) {
        return true;
      }
    }
    if (sub._dirty) {
      return true;
    }
    return false;
  }
  function refreshComputed(computed5) {
    if (computed5.flags & 4 && !(computed5.flags & 16)) {
      return;
    }
    computed5.flags &= ~16;
    if (computed5.globalVersion === globalVersion) {
      return;
    }
    computed5.globalVersion = globalVersion;
    const dep = computed5.dep;
    computed5.flags |= 2;
    if (dep.version > 0 && !computed5.isSSR && computed5.deps && !isDirty(computed5)) {
      computed5.flags &= ~2;
      return;
    }
    const prevSub = activeSub;
    const prevShouldTrack = shouldTrack;
    activeSub = computed5;
    shouldTrack = true;
    try {
      prepareDeps(computed5);
      const value = computed5.fn(computed5._value);
      if (dep.version === 0 || hasChanged(value, computed5._value)) {
        computed5._value = value;
        dep.version++;
      }
    } catch (err) {
      dep.version++;
      throw err;
    } finally {
      activeSub = prevSub;
      shouldTrack = prevShouldTrack;
      cleanupDeps(computed5);
      computed5.flags &= ~2;
    }
  }
  function removeSub(link, soft = false) {
    const { dep, prevSub, nextSub } = link;
    if (prevSub) {
      prevSub.nextSub = nextSub;
      link.prevSub = void 0;
    }
    if (nextSub) {
      nextSub.prevSub = prevSub;
      link.nextSub = void 0;
    }
    if (dep.subsHead === link) {
      dep.subsHead = nextSub;
    }
    if (dep.subs === link) {
      dep.subs = prevSub;
      if (!prevSub && dep.computed) {
        dep.computed.flags &= ~4;
        for (let l = dep.computed.deps; l; l = l.nextDep) {
          removeSub(l, true);
        }
      }
    }
    if (!soft && !--dep.sc && dep.map) {
      dep.map.delete(dep.key);
    }
  }
  function removeDep(link) {
    const { prevDep, nextDep } = link;
    if (prevDep) {
      prevDep.nextDep = nextDep;
      link.prevDep = void 0;
    }
    if (nextDep) {
      nextDep.prevDep = prevDep;
      link.nextDep = void 0;
    }
  }
  var shouldTrack = true;
  var trackStack = [];
  function pauseTracking() {
    trackStack.push(shouldTrack);
    shouldTrack = false;
  }
  function resetTracking() {
    const last = trackStack.pop();
    shouldTrack = last === void 0 ? true : last;
  }
  function cleanupEffect(e) {
    const { cleanup } = e;
    e.cleanup = void 0;
    if (cleanup) {
      const prevSub = activeSub;
      activeSub = void 0;
      try {
        cleanup();
      } finally {
        activeSub = prevSub;
      }
    }
  }
  var globalVersion = 0;
  var Link = class {
    constructor(sub, dep) {
      this.sub = sub;
      this.dep = dep;
      this.version = dep.version;
      this.nextDep = this.prevDep = this.nextSub = this.prevSub = this.prevActiveLink = void 0;
    }
  };
  var Dep = class {
    constructor(computed5) {
      this.computed = computed5;
      this.version = 0;
      this.activeLink = void 0;
      this.subs = void 0;
      this.map = void 0;
      this.key = void 0;
      this.sc = 0;
      if (true) {
        this.subsHead = void 0;
      }
    }
    track(debugInfo) {
      if (!activeSub || !shouldTrack || activeSub === this.computed) {
        return;
      }
      let link = this.activeLink;
      if (link === void 0 || link.sub !== activeSub) {
        link = this.activeLink = new Link(activeSub, this);
        if (!activeSub.deps) {
          activeSub.deps = activeSub.depsTail = link;
        } else {
          link.prevDep = activeSub.depsTail;
          activeSub.depsTail.nextDep = link;
          activeSub.depsTail = link;
        }
        addSub(link);
      } else if (link.version === -1) {
        link.version = this.version;
        if (link.nextDep) {
          const next = link.nextDep;
          next.prevDep = link.prevDep;
          if (link.prevDep) {
            link.prevDep.nextDep = next;
          }
          link.prevDep = activeSub.depsTail;
          link.nextDep = void 0;
          activeSub.depsTail.nextDep = link;
          activeSub.depsTail = link;
          if (activeSub.deps === link) {
            activeSub.deps = next;
          }
        }
      }
      if (activeSub.onTrack) {
        activeSub.onTrack(
          extend(
            {
              effect: activeSub
            },
            debugInfo
          )
        );
      }
      return link;
    }
    trigger(debugInfo) {
      this.version++;
      globalVersion++;
      this.notify(debugInfo);
    }
    notify(debugInfo) {
      startBatch();
      try {
        if (true) {
          for (let head = this.subsHead; head; head = head.nextSub) {
            if (head.sub.onTrigger && !(head.sub.flags & 8)) {
              head.sub.onTrigger(
                extend(
                  {
                    effect: head.sub
                  },
                  debugInfo
                )
              );
            }
          }
        }
        for (let link = this.subs; link; link = link.prevSub) {
          if (link.sub.notify()) {
            ;
            link.sub.dep.notify();
          }
        }
      } finally {
        endBatch();
      }
    }
  };
  function addSub(link) {
    link.dep.sc++;
    if (link.sub.flags & 4) {
      const computed5 = link.dep.computed;
      if (computed5 && !link.dep.subs) {
        computed5.flags |= 4 | 16;
        for (let l = computed5.deps; l; l = l.nextDep) {
          addSub(l);
        }
      }
      const currentTail = link.dep.subs;
      if (currentTail !== link) {
        link.prevSub = currentTail;
        if (currentTail)
          currentTail.nextSub = link;
      }
      if (link.dep.subsHead === void 0) {
        link.dep.subsHead = link;
      }
      link.dep.subs = link;
    }
  }
  var targetMap = /* @__PURE__ */ new WeakMap();
  var ITERATE_KEY = Symbol(
    true ? "Object iterate" : ""
  );
  var MAP_KEY_ITERATE_KEY = Symbol(
    true ? "Map keys iterate" : ""
  );
  var ARRAY_ITERATE_KEY = Symbol(
    true ? "Array iterate" : ""
  );
  function track(target, type, key) {
    if (shouldTrack && activeSub) {
      let depsMap = targetMap.get(target);
      if (!depsMap) {
        targetMap.set(target, depsMap = /* @__PURE__ */ new Map());
      }
      let dep = depsMap.get(key);
      if (!dep) {
        depsMap.set(key, dep = new Dep());
        dep.map = depsMap;
        dep.key = key;
      }
      if (true) {
        dep.track({
          target,
          type,
          key
        });
      } else {
        dep.track();
      }
    }
  }
  function trigger(target, type, key, newValue, oldValue, oldTarget) {
    const depsMap = targetMap.get(target);
    if (!depsMap) {
      globalVersion++;
      return;
    }
    const run = (dep) => {
      if (dep) {
        if (true) {
          dep.trigger({
            target,
            type,
            key,
            newValue,
            oldValue,
            oldTarget
          });
        } else {
          dep.trigger();
        }
      }
    };
    startBatch();
    if (type === "clear") {
      depsMap.forEach(run);
    } else {
      const targetIsArray = isArray(target);
      const isArrayIndex = targetIsArray && isIntegerKey(key);
      if (targetIsArray && key === "length") {
        const newLength = Number(newValue);
        depsMap.forEach((dep, key2) => {
          if (key2 === "length" || key2 === ARRAY_ITERATE_KEY || !isSymbol(key2) && key2 >= newLength) {
            run(dep);
          }
        });
      } else {
        if (key !== void 0 || depsMap.has(void 0)) {
          run(depsMap.get(key));
        }
        if (isArrayIndex) {
          run(depsMap.get(ARRAY_ITERATE_KEY));
        }
        switch (type) {
          case "add":
            if (!targetIsArray) {
              run(depsMap.get(ITERATE_KEY));
              if (isMap(target)) {
                run(depsMap.get(MAP_KEY_ITERATE_KEY));
              }
            } else if (isArrayIndex) {
              run(depsMap.get("length"));
            }
            break;
          case "delete":
            if (!targetIsArray) {
              run(depsMap.get(ITERATE_KEY));
              if (isMap(target)) {
                run(depsMap.get(MAP_KEY_ITERATE_KEY));
              }
            }
            break;
          case "set":
            if (isMap(target)) {
              run(depsMap.get(ITERATE_KEY));
            }
            break;
        }
      }
    }
    endBatch();
  }
  function reactiveReadArray(array) {
    const raw = toRaw(array);
    if (raw === array)
      return raw;
    track(raw, "iterate", ARRAY_ITERATE_KEY);
    return isShallow(array) ? raw : raw.map(toReactive);
  }
  function shallowReadArray(arr) {
    track(arr = toRaw(arr), "iterate", ARRAY_ITERATE_KEY);
    return arr;
  }
  var arrayInstrumentations = {
    __proto__: null,
    [Symbol.iterator]() {
      return iterator(this, Symbol.iterator, toReactive);
    },
    concat(...args) {
      return reactiveReadArray(this).concat(
        ...args.map((x) => isArray(x) ? reactiveReadArray(x) : x)
      );
    },
    entries() {
      return iterator(this, "entries", (value) => {
        value[1] = toReactive(value[1]);
        return value;
      });
    },
    every(fn2, thisArg) {
      return apply(this, "every", fn2, thisArg, void 0, arguments);
    },
    filter(fn2, thisArg) {
      return apply(this, "filter", fn2, thisArg, (v) => v.map(toReactive), arguments);
    },
    find(fn2, thisArg) {
      return apply(this, "find", fn2, thisArg, toReactive, arguments);
    },
    findIndex(fn2, thisArg) {
      return apply(this, "findIndex", fn2, thisArg, void 0, arguments);
    },
    findLast(fn2, thisArg) {
      return apply(this, "findLast", fn2, thisArg, toReactive, arguments);
    },
    findLastIndex(fn2, thisArg) {
      return apply(this, "findLastIndex", fn2, thisArg, void 0, arguments);
    },
    forEach(fn2, thisArg) {
      return apply(this, "forEach", fn2, thisArg, void 0, arguments);
    },
    includes(...args) {
      return searchProxy(this, "includes", args);
    },
    indexOf(...args) {
      return searchProxy(this, "indexOf", args);
    },
    join(separator) {
      return reactiveReadArray(this).join(separator);
    },
    lastIndexOf(...args) {
      return searchProxy(this, "lastIndexOf", args);
    },
    map(fn2, thisArg) {
      return apply(this, "map", fn2, thisArg, void 0, arguments);
    },
    pop() {
      return noTracking(this, "pop");
    },
    push(...args) {
      return noTracking(this, "push", args);
    },
    reduce(fn2, ...args) {
      return reduce(this, "reduce", fn2, args);
    },
    reduceRight(fn2, ...args) {
      return reduce(this, "reduceRight", fn2, args);
    },
    shift() {
      return noTracking(this, "shift");
    },
    some(fn2, thisArg) {
      return apply(this, "some", fn2, thisArg, void 0, arguments);
    },
    splice(...args) {
      return noTracking(this, "splice", args);
    },
    toReversed() {
      return reactiveReadArray(this).toReversed();
    },
    toSorted(comparer) {
      return reactiveReadArray(this).toSorted(comparer);
    },
    toSpliced(...args) {
      return reactiveReadArray(this).toSpliced(...args);
    },
    unshift(...args) {
      return noTracking(this, "unshift", args);
    },
    values() {
      return iterator(this, "values", toReactive);
    }
  };
  function iterator(self2, method, wrapValue) {
    const arr = shallowReadArray(self2);
    const iter = arr[method]();
    if (arr !== self2 && !isShallow(self2)) {
      iter._next = iter.next;
      iter.next = () => {
        const result = iter._next();
        if (result.value) {
          result.value = wrapValue(result.value);
        }
        return result;
      };
    }
    return iter;
  }
  var arrayProto = Array.prototype;
  function apply(self2, method, fn2, thisArg, wrappedRetFn, args) {
    const arr = shallowReadArray(self2);
    const needsWrap = arr !== self2 && !isShallow(self2);
    const methodFn = arr[method];
    if (methodFn !== arrayProto[method]) {
      const result2 = methodFn.apply(self2, args);
      return needsWrap ? toReactive(result2) : result2;
    }
    let wrappedFn = fn2;
    if (arr !== self2) {
      if (needsWrap) {
        wrappedFn = function(item, index) {
          return fn2.call(this, toReactive(item), index, self2);
        };
      } else if (fn2.length > 2) {
        wrappedFn = function(item, index) {
          return fn2.call(this, item, index, self2);
        };
      }
    }
    const result = methodFn.call(arr, wrappedFn, thisArg);
    return needsWrap && wrappedRetFn ? wrappedRetFn(result) : result;
  }
  function reduce(self2, method, fn2, args) {
    const arr = shallowReadArray(self2);
    let wrappedFn = fn2;
    if (arr !== self2) {
      if (!isShallow(self2)) {
        wrappedFn = function(acc, item, index) {
          return fn2.call(this, acc, toReactive(item), index, self2);
        };
      } else if (fn2.length > 3) {
        wrappedFn = function(acc, item, index) {
          return fn2.call(this, acc, item, index, self2);
        };
      }
    }
    return arr[method](wrappedFn, ...args);
  }
  function searchProxy(self2, method, args) {
    const arr = toRaw(self2);
    track(arr, "iterate", ARRAY_ITERATE_KEY);
    const res = arr[method](...args);
    if ((res === -1 || res === false) && isProxy(args[0])) {
      args[0] = toRaw(args[0]);
      return arr[method](...args);
    }
    return res;
  }
  function noTracking(self2, method, args = []) {
    pauseTracking();
    startBatch();
    const res = toRaw(self2)[method].apply(self2, args);
    endBatch();
    resetTracking();
    return res;
  }
  var isNonTrackableKeys = /* @__PURE__ */ makeMap(`__proto__,__v_isRef,__isVue`);
  var builtInSymbols = new Set(
    /* @__PURE__ */ Object.getOwnPropertyNames(Symbol).filter((key) => key !== "arguments" && key !== "caller").map((key) => Symbol[key]).filter(isSymbol)
  );
  function hasOwnProperty2(key) {
    if (!isSymbol(key))
      key = String(key);
    const obj = toRaw(this);
    track(obj, "has", key);
    return obj.hasOwnProperty(key);
  }
  var BaseReactiveHandler = class {
    constructor(_isReadonly = false, _isShallow = false) {
      this._isReadonly = _isReadonly;
      this._isShallow = _isShallow;
    }
    get(target, key, receiver) {
      const isReadonly22 = this._isReadonly, isShallow22 = this._isShallow;
      if (key === "__v_isReactive") {
        return !isReadonly22;
      } else if (key === "__v_isReadonly") {
        return isReadonly22;
      } else if (key === "__v_isShallow") {
        return isShallow22;
      } else if (key === "__v_raw") {
        if (receiver === (isReadonly22 ? isShallow22 ? shallowReadonlyMap : readonlyMap : isShallow22 ? shallowReactiveMap : reactiveMap).get(target) || Object.getPrototypeOf(target) === Object.getPrototypeOf(receiver)) {
          return target;
        }
        return;
      }
      const targetIsArray = isArray(target);
      if (!isReadonly22) {
        let fn2;
        if (targetIsArray && (fn2 = arrayInstrumentations[key])) {
          return fn2;
        }
        if (key === "hasOwnProperty") {
          return hasOwnProperty2;
        }
      }
      const res = Reflect.get(
        target,
        key,
        isRef2(target) ? target : receiver
      );
      if (isSymbol(key) ? builtInSymbols.has(key) : isNonTrackableKeys(key)) {
        return res;
      }
      if (!isReadonly22) {
        track(target, "get", key);
      }
      if (isShallow22) {
        return res;
      }
      if (isRef2(res)) {
        return targetIsArray && isIntegerKey(key) ? res : res.value;
      }
      if (isObject(res)) {
        return isReadonly22 ? readonly(res) : reactive(res);
      }
      return res;
    }
  };
  var MutableReactiveHandler = class extends BaseReactiveHandler {
    constructor(isShallow22 = false) {
      super(false, isShallow22);
    }
    set(target, key, value, receiver) {
      let oldValue = target[key];
      if (!this._isShallow) {
        const isOldValueReadonly = isReadonly(oldValue);
        if (!isShallow(value) && !isReadonly(value)) {
          oldValue = toRaw(oldValue);
          value = toRaw(value);
        }
        if (!isArray(target) && isRef2(oldValue) && !isRef2(value)) {
          if (isOldValueReadonly) {
            return false;
          } else {
            oldValue.value = value;
            return true;
          }
        }
      }
      const hadKey = isArray(target) && isIntegerKey(key) ? Number(key) < target.length : hasOwn(target, key);
      const result = Reflect.set(
        target,
        key,
        value,
        isRef2(target) ? target : receiver
      );
      if (target === toRaw(receiver)) {
        if (!hadKey) {
          trigger(target, "add", key, value);
        } else if (hasChanged(value, oldValue)) {
          trigger(target, "set", key, value, oldValue);
        }
      }
      return result;
    }
    deleteProperty(target, key) {
      const hadKey = hasOwn(target, key);
      const oldValue = target[key];
      const result = Reflect.deleteProperty(target, key);
      if (result && hadKey) {
        trigger(target, "delete", key, void 0, oldValue);
      }
      return result;
    }
    has(target, key) {
      const result = Reflect.has(target, key);
      if (!isSymbol(key) || !builtInSymbols.has(key)) {
        track(target, "has", key);
      }
      return result;
    }
    ownKeys(target) {
      track(
        target,
        "iterate",
        isArray(target) ? "length" : ITERATE_KEY
      );
      return Reflect.ownKeys(target);
    }
  };
  var ReadonlyReactiveHandler = class extends BaseReactiveHandler {
    constructor(isShallow22 = false) {
      super(true, isShallow22);
    }
    set(target, key) {
      if (true) {
        warn(
          `Set operation on key "${String(key)}" failed: target is readonly.`,
          target
        );
      }
      return true;
    }
    deleteProperty(target, key) {
      if (true) {
        warn(
          `Delete operation on key "${String(key)}" failed: target is readonly.`,
          target
        );
      }
      return true;
    }
  };
  var mutableHandlers = /* @__PURE__ */ new MutableReactiveHandler();
  var readonlyHandlers = /* @__PURE__ */ new ReadonlyReactiveHandler();
  var shallowReactiveHandlers = /* @__PURE__ */ new MutableReactiveHandler(true);
  var shallowReadonlyHandlers = /* @__PURE__ */ new ReadonlyReactiveHandler(true);
  var toShallow = (value) => value;
  var getProto = (v) => Reflect.getPrototypeOf(v);
  function createIterableMethod(method, isReadonly22, isShallow22) {
    return function(...args) {
      const target = this["__v_raw"];
      const rawTarget = toRaw(target);
      const targetIsMap = isMap(rawTarget);
      const isPair = method === "entries" || method === Symbol.iterator && targetIsMap;
      const isKeyOnly = method === "keys" && targetIsMap;
      const innerIterator = target[method](...args);
      const wrap = isShallow22 ? toShallow : isReadonly22 ? toReadonly : toReactive;
      !isReadonly22 && track(
        rawTarget,
        "iterate",
        isKeyOnly ? MAP_KEY_ITERATE_KEY : ITERATE_KEY
      );
      return {
        next() {
          const { value, done } = innerIterator.next();
          return done ? { value, done } : {
            value: isPair ? [wrap(value[0]), wrap(value[1])] : wrap(value),
            done
          };
        },
        [Symbol.iterator]() {
          return this;
        }
      };
    };
  }
  function createReadonlyMethod(type) {
    return function(...args) {
      if (true) {
        const key = args[0] ? `on key "${args[0]}" ` : ``;
        warn(
          `${capitalize(type)} operation ${key}failed: target is readonly.`,
          toRaw(this)
        );
      }
      return type === "delete" ? false : type === "clear" ? void 0 : this;
    };
  }
  function createInstrumentations(readonly3, shallow) {
    const instrumentations = {
      get(key) {
        const target = this["__v_raw"];
        const rawTarget = toRaw(target);
        const rawKey = toRaw(key);
        if (!readonly3) {
          if (hasChanged(key, rawKey)) {
            track(rawTarget, "get", key);
          }
          track(rawTarget, "get", rawKey);
        }
        const { has: has2 } = getProto(rawTarget);
        const wrap = shallow ? toShallow : readonly3 ? toReadonly : toReactive;
        if (has2.call(rawTarget, key)) {
          return wrap(target.get(key));
        } else if (has2.call(rawTarget, rawKey)) {
          return wrap(target.get(rawKey));
        } else if (target !== rawTarget) {
          target.get(key);
        }
      },
      get size() {
        const target = this["__v_raw"];
        !readonly3 && track(toRaw(target), "iterate", ITERATE_KEY);
        return Reflect.get(target, "size", target);
      },
      has(key) {
        const target = this["__v_raw"];
        const rawTarget = toRaw(target);
        const rawKey = toRaw(key);
        if (!readonly3) {
          if (hasChanged(key, rawKey)) {
            track(rawTarget, "has", key);
          }
          track(rawTarget, "has", rawKey);
        }
        return key === rawKey ? target.has(key) : target.has(key) || target.has(rawKey);
      },
      forEach(callback, thisArg) {
        const observed = this;
        const target = observed["__v_raw"];
        const rawTarget = toRaw(target);
        const wrap = shallow ? toShallow : readonly3 ? toReadonly : toReactive;
        !readonly3 && track(rawTarget, "iterate", ITERATE_KEY);
        return target.forEach((value, key) => {
          return callback.call(thisArg, wrap(value), wrap(key), observed);
        });
      }
    };
    extend(
      instrumentations,
      readonly3 ? {
        add: createReadonlyMethod("add"),
        set: createReadonlyMethod("set"),
        delete: createReadonlyMethod("delete"),
        clear: createReadonlyMethod("clear")
      } : {
        add(value) {
          if (!shallow && !isShallow(value) && !isReadonly(value)) {
            value = toRaw(value);
          }
          const target = toRaw(this);
          const proto = getProto(target);
          const hadKey = proto.has.call(target, value);
          if (!hadKey) {
            target.add(value);
            trigger(target, "add", value, value);
          }
          return this;
        },
        set(key, value) {
          if (!shallow && !isShallow(value) && !isReadonly(value)) {
            value = toRaw(value);
          }
          const target = toRaw(this);
          const { has: has2, get: get2 } = getProto(target);
          let hadKey = has2.call(target, key);
          if (!hadKey) {
            key = toRaw(key);
            hadKey = has2.call(target, key);
          } else if (true) {
            checkIdentityKeys(target, has2, key);
          }
          const oldValue = get2.call(target, key);
          target.set(key, value);
          if (!hadKey) {
            trigger(target, "add", key, value);
          } else if (hasChanged(value, oldValue)) {
            trigger(target, "set", key, value, oldValue);
          }
          return this;
        },
        delete(key) {
          const target = toRaw(this);
          const { has: has2, get: get2 } = getProto(target);
          let hadKey = has2.call(target, key);
          if (!hadKey) {
            key = toRaw(key);
            hadKey = has2.call(target, key);
          } else if (true) {
            checkIdentityKeys(target, has2, key);
          }
          const oldValue = get2 ? get2.call(target, key) : void 0;
          const result = target.delete(key);
          if (hadKey) {
            trigger(target, "delete", key, void 0, oldValue);
          }
          return result;
        },
        clear() {
          const target = toRaw(this);
          const hadItems = target.size !== 0;
          const oldTarget = true ? isMap(target) ? new Map(target) : new Set(target) : void 0;
          const result = target.clear();
          if (hadItems) {
            trigger(
              target,
              "clear",
              void 0,
              void 0,
              oldTarget
            );
          }
          return result;
        }
      }
    );
    const iteratorMethods = [
      "keys",
      "values",
      "entries",
      Symbol.iterator
    ];
    iteratorMethods.forEach((method) => {
      instrumentations[method] = createIterableMethod(method, readonly3, shallow);
    });
    return instrumentations;
  }
  function createInstrumentationGetter(isReadonly22, shallow) {
    const instrumentations = createInstrumentations(isReadonly22, shallow);
    return (target, key, receiver) => {
      if (key === "__v_isReactive") {
        return !isReadonly22;
      } else if (key === "__v_isReadonly") {
        return isReadonly22;
      } else if (key === "__v_raw") {
        return target;
      }
      return Reflect.get(
        hasOwn(instrumentations, key) && key in target ? instrumentations : target,
        key,
        receiver
      );
    };
  }
  var mutableCollectionHandlers = {
    get: /* @__PURE__ */ createInstrumentationGetter(false, false)
  };
  var shallowCollectionHandlers = {
    get: /* @__PURE__ */ createInstrumentationGetter(false, true)
  };
  var readonlyCollectionHandlers = {
    get: /* @__PURE__ */ createInstrumentationGetter(true, false)
  };
  var shallowReadonlyCollectionHandlers = {
    get: /* @__PURE__ */ createInstrumentationGetter(true, true)
  };
  function checkIdentityKeys(target, has2, key) {
    const rawKey = toRaw(key);
    if (rawKey !== key && has2.call(target, rawKey)) {
      const type = toRawType(target);
      warn(
        `Reactive ${type} contains both the raw and reactive versions of the same object${type === `Map` ? ` as keys` : ``}, which can lead to inconsistencies. Avoid differentiating between the raw and reactive versions of an object and only use the reactive version if possible.`
      );
    }
  }
  var reactiveMap = /* @__PURE__ */ new WeakMap();
  var shallowReactiveMap = /* @__PURE__ */ new WeakMap();
  var readonlyMap = /* @__PURE__ */ new WeakMap();
  var shallowReadonlyMap = /* @__PURE__ */ new WeakMap();
  function targetTypeMap(rawType) {
    switch (rawType) {
      case "Object":
      case "Array":
        return 1;
      case "Map":
      case "Set":
      case "WeakMap":
      case "WeakSet":
        return 2;
      default:
        return 0;
    }
  }
  function getTargetType(value) {
    return value["__v_skip"] || !Object.isExtensible(value) ? 0 : targetTypeMap(toRawType(value));
  }
  function reactive(target) {
    if (isReadonly(target)) {
      return target;
    }
    return createReactiveObject(
      target,
      false,
      mutableHandlers,
      mutableCollectionHandlers,
      reactiveMap
    );
  }
  function shallowReactive(target) {
    return createReactiveObject(
      target,
      false,
      shallowReactiveHandlers,
      shallowCollectionHandlers,
      shallowReactiveMap
    );
  }
  function readonly(target) {
    return createReactiveObject(
      target,
      true,
      readonlyHandlers,
      readonlyCollectionHandlers,
      readonlyMap
    );
  }
  function shallowReadonly(target) {
    return createReactiveObject(
      target,
      true,
      shallowReadonlyHandlers,
      shallowReadonlyCollectionHandlers,
      shallowReadonlyMap
    );
  }
  function createReactiveObject(target, isReadonly22, baseHandlers, collectionHandlers, proxyMap) {
    if (!isObject(target)) {
      if (true) {
        warn(
          `value cannot be made ${isReadonly22 ? "readonly" : "reactive"}: ${String(
            target
          )}`
        );
      }
      return target;
    }
    if (target["__v_raw"] && !(isReadonly22 && target["__v_isReactive"])) {
      return target;
    }
    const existingProxy = proxyMap.get(target);
    if (existingProxy) {
      return existingProxy;
    }
    const targetType = getTargetType(target);
    if (targetType === 0) {
      return target;
    }
    const proxy = new Proxy(
      target,
      targetType === 2 ? collectionHandlers : baseHandlers
    );
    proxyMap.set(target, proxy);
    return proxy;
  }
  function isReactive(value) {
    if (isReadonly(value)) {
      return isReactive(value["__v_raw"]);
    }
    return !!(value && value["__v_isReactive"]);
  }
  function isReadonly(value) {
    return !!(value && value["__v_isReadonly"]);
  }
  function isShallow(value) {
    return !!(value && value["__v_isShallow"]);
  }
  function isProxy(value) {
    return value ? !!value["__v_raw"] : false;
  }
  function toRaw(observed) {
    const raw = observed && observed["__v_raw"];
    return raw ? toRaw(raw) : observed;
  }
  function markRaw(value) {
    if (!hasOwn(value, "__v_skip") && Object.isExtensible(value)) {
      def(value, "__v_skip", true);
    }
    return value;
  }
  var toReactive = (value) => isObject(value) ? reactive(value) : value;
  var toReadonly = (value) => isObject(value) ? readonly(value) : value;
  function isRef2(r) {
    return r ? r["__v_isRef"] === true : false;
  }
  function ref(value) {
    return createRef(value, false);
  }
  function createRef(rawValue, shallow) {
    if (isRef2(rawValue)) {
      return rawValue;
    }
    return new RefImpl(rawValue, shallow);
  }
  var RefImpl = class {
    constructor(value, isShallow22) {
      this.dep = new Dep();
      this["__v_isRef"] = true;
      this["__v_isShallow"] = false;
      this._rawValue = isShallow22 ? value : toRaw(value);
      this._value = isShallow22 ? value : toReactive(value);
      this["__v_isShallow"] = isShallow22;
    }
    get value() {
      if (true) {
        this.dep.track({
          target: this,
          type: "get",
          key: "value"
        });
      } else {
        this.dep.track();
      }
      return this._value;
    }
    set value(newValue) {
      const oldValue = this._rawValue;
      const useDirectValue = this["__v_isShallow"] || isShallow(newValue) || isReadonly(newValue);
      newValue = useDirectValue ? newValue : toRaw(newValue);
      if (hasChanged(newValue, oldValue)) {
        this._rawValue = newValue;
        this._value = useDirectValue ? newValue : toReactive(newValue);
        if (true) {
          this.dep.trigger({
            target: this,
            type: "set",
            key: "value",
            newValue,
            oldValue
          });
        } else {
          this.dep.trigger();
        }
      }
    }
  };
  function unref(ref22) {
    return isRef2(ref22) ? ref22.value : ref22;
  }
  var shallowUnwrapHandlers = {
    get: (target, key, receiver) => key === "__v_raw" ? target : unref(Reflect.get(target, key, receiver)),
    set: (target, key, value, receiver) => {
      const oldValue = target[key];
      if (isRef2(oldValue) && !isRef2(value)) {
        oldValue.value = value;
        return true;
      } else {
        return Reflect.set(target, key, value, receiver);
      }
    }
  };
  function proxyRefs(objectWithRefs) {
    return isReactive(objectWithRefs) ? objectWithRefs : new Proxy(objectWithRefs, shallowUnwrapHandlers);
  }
  var ComputedRefImpl = class {
    constructor(fn2, setter, isSSR) {
      this.fn = fn2;
      this.setter = setter;
      this._value = void 0;
      this.dep = new Dep(this);
      this.__v_isRef = true;
      this.deps = void 0;
      this.depsTail = void 0;
      this.flags = 16;
      this.globalVersion = globalVersion - 1;
      this.next = void 0;
      this.effect = this;
      this["__v_isReadonly"] = !setter;
      this.isSSR = isSSR;
    }
    notify() {
      this.flags |= 16;
      if (!(this.flags & 8) && activeSub !== this) {
        batch(this, true);
        return true;
      } else if (true)
        ;
    }
    get value() {
      const link = true ? this.dep.track({
        target: this,
        type: "get",
        key: "value"
      }) : this.dep.track();
      refreshComputed(this);
      if (link) {
        link.version = this.dep.version;
      }
      return this._value;
    }
    set value(newValue) {
      if (this.setter) {
        this.setter(newValue);
      } else if (true) {
        warn("Write operation failed: computed value is readonly");
      }
    }
  };
  function computed(getterOrOptions, debugOptions, isSSR = false) {
    let getter;
    let setter;
    if (isFunction(getterOrOptions)) {
      getter = getterOrOptions;
    } else {
      getter = getterOrOptions.get;
      setter = getterOrOptions.set;
    }
    const cRef = new ComputedRefImpl(getter, setter, isSSR);
    if (debugOptions && !isSSR) {
      cRef.onTrack = debugOptions.onTrack;
      cRef.onTrigger = debugOptions.onTrigger;
    }
    return cRef;
  }
  var INITIAL_WATCHER_VALUE = {};
  var cleanupMap = /* @__PURE__ */ new WeakMap();
  var activeWatcher = void 0;
  function onWatcherCleanup(cleanupFn, failSilently = false, owner = activeWatcher) {
    if (owner) {
      let cleanups = cleanupMap.get(owner);
      if (!cleanups)
        cleanupMap.set(owner, cleanups = []);
      cleanups.push(cleanupFn);
    } else if (!failSilently) {
      warn(
        `onWatcherCleanup() was called when there was no active watcher to associate with.`
      );
    }
  }
  function watch(source, cb, options = EMPTY_OBJ) {
    const { immediate, deep, once, scheduler, augmentJob, call } = options;
    const warnInvalidSource = (s) => {
      (options.onWarn || warn)(
        `Invalid watch source: `,
        s,
        `A watch source can only be a getter/effect function, a ref, a reactive object, or an array of these types.`
      );
    };
    const reactiveGetter = (source2) => {
      if (deep)
        return source2;
      if (isShallow(source2) || deep === false || deep === 0)
        return traverse(source2, 1);
      return traverse(source2);
    };
    let effect6;
    let getter;
    let cleanup;
    let boundCleanup;
    let forceTrigger = false;
    let isMultiSource = false;
    if (isRef2(source)) {
      getter = () => source.value;
      forceTrigger = isShallow(source);
    } else if (isReactive(source)) {
      getter = () => reactiveGetter(source);
      forceTrigger = true;
    } else if (isArray(source)) {
      isMultiSource = true;
      forceTrigger = source.some((s) => isReactive(s) || isShallow(s));
      getter = () => source.map((s) => {
        if (isRef2(s)) {
          return s.value;
        } else if (isReactive(s)) {
          return reactiveGetter(s);
        } else if (isFunction(s)) {
          return call ? call(s, 2) : s();
        } else {
          warnInvalidSource(s);
        }
      });
    } else if (isFunction(source)) {
      if (cb) {
        getter = call ? () => call(source, 2) : source;
      } else {
        getter = () => {
          if (cleanup) {
            pauseTracking();
            try {
              cleanup();
            } finally {
              resetTracking();
            }
          }
          const currentEffect = activeWatcher;
          activeWatcher = effect6;
          try {
            return call ? call(source, 3, [boundCleanup]) : source(boundCleanup);
          } finally {
            activeWatcher = currentEffect;
          }
        };
      }
    } else {
      getter = NOOP;
      warnInvalidSource(source);
    }
    if (cb && deep) {
      const baseGetter = getter;
      const depth = deep === true ? Infinity : deep;
      getter = () => traverse(baseGetter(), depth);
    }
    const scope = getCurrentScope();
    const watchHandle = () => {
      effect6.stop();
      if (scope) {
        remove(scope.effects, effect6);
      }
    };
    if (once && cb) {
      const _cb = cb;
      cb = (...args) => {
        _cb(...args);
        watchHandle();
      };
    }
    let oldValue = isMultiSource ? new Array(source.length).fill(INITIAL_WATCHER_VALUE) : INITIAL_WATCHER_VALUE;
    const job = (immediateFirstRun) => {
      if (!(effect6.flags & 1) || !effect6.dirty && !immediateFirstRun) {
        return;
      }
      if (cb) {
        const newValue = effect6.run();
        if (deep || forceTrigger || (isMultiSource ? newValue.some((v, i) => hasChanged(v, oldValue[i])) : hasChanged(newValue, oldValue))) {
          if (cleanup) {
            cleanup();
          }
          const currentWatcher = activeWatcher;
          activeWatcher = effect6;
          try {
            const args = [
              newValue,
              oldValue === INITIAL_WATCHER_VALUE ? void 0 : isMultiSource && oldValue[0] === INITIAL_WATCHER_VALUE ? [] : oldValue,
              boundCleanup
            ];
            call ? call(cb, 3, args) : cb(...args);
            oldValue = newValue;
          } finally {
            activeWatcher = currentWatcher;
          }
        }
      } else {
        effect6.run();
      }
    };
    if (augmentJob) {
      augmentJob(job);
    }
    effect6 = new ReactiveEffect(getter);
    effect6.scheduler = scheduler ? () => scheduler(job, false) : job;
    boundCleanup = (fn2) => onWatcherCleanup(fn2, false, effect6);
    cleanup = effect6.onStop = () => {
      const cleanups = cleanupMap.get(effect6);
      if (cleanups) {
        if (call) {
          call(cleanups, 4);
        } else {
          for (const cleanup2 of cleanups)
            cleanup2();
        }
        cleanupMap.delete(effect6);
      }
    };
    if (true) {
      effect6.onTrack = options.onTrack;
      effect6.onTrigger = options.onTrigger;
    }
    if (cb) {
      if (immediate) {
        job(true);
      } else {
        oldValue = effect6.run();
      }
    } else if (scheduler) {
      scheduler(job.bind(null, true), true);
    } else {
      effect6.run();
    }
    watchHandle.pause = effect6.pause.bind(effect6);
    watchHandle.resume = effect6.resume.bind(effect6);
    watchHandle.stop = watchHandle;
    return watchHandle;
  }
  function traverse(value, depth = Infinity, seen) {
    if (depth <= 0 || !isObject(value) || value["__v_skip"]) {
      return value;
    }
    seen = seen || /* @__PURE__ */ new Set();
    if (seen.has(value)) {
      return value;
    }
    seen.add(value);
    depth--;
    if (isRef2(value)) {
      traverse(value.value, depth, seen);
    } else if (isArray(value)) {
      for (let i = 0; i < value.length; i++) {
        traverse(value[i], depth, seen);
      }
    } else if (isSet(value) || isMap(value)) {
      value.forEach((v) => {
        traverse(v, depth, seen);
      });
    } else if (isPlainObject(value)) {
      for (const key in value) {
        traverse(value[key], depth, seen);
      }
      for (const key of Object.getOwnPropertySymbols(value)) {
        if (Object.prototype.propertyIsEnumerable.call(value, key)) {
          traverse(value[key], depth, seen);
        }
      }
    }
    return value;
  }

  // ../powerpro/node_modules/@vue/runtime-core/dist/runtime-core.esm-bundler.js
  var stack = [];
  function pushWarningContext(vnode) {
    stack.push(vnode);
  }
  function popWarningContext() {
    stack.pop();
  }
  var isWarning = false;
  function warn$1(msg, ...args) {
    if (isWarning)
      return;
    isWarning = true;
    pauseTracking();
    const instance = stack.length ? stack[stack.length - 1].component : null;
    const appWarnHandler = instance && instance.appContext.config.warnHandler;
    const trace = getComponentTrace();
    if (appWarnHandler) {
      callWithErrorHandling(
        appWarnHandler,
        instance,
        11,
        [
          msg + args.map((a) => {
            var _a, _b;
            return (_b = (_a = a.toString) == null ? void 0 : _a.call(a)) != null ? _b : JSON.stringify(a);
          }).join(""),
          instance && instance.proxy,
          trace.map(
            ({ vnode }) => `at <${formatComponentName(instance, vnode.type)}>`
          ).join("\n"),
          trace
        ]
      );
    } else {
      const warnArgs = [`[Vue warn]: ${msg}`, ...args];
      if (trace.length && true) {
        warnArgs.push(`
`, ...formatTrace(trace));
      }
      console.warn(...warnArgs);
    }
    resetTracking();
    isWarning = false;
  }
  function getComponentTrace() {
    let currentVNode = stack[stack.length - 1];
    if (!currentVNode) {
      return [];
    }
    const normalizedStack = [];
    while (currentVNode) {
      const last = normalizedStack[0];
      if (last && last.vnode === currentVNode) {
        last.recurseCount++;
      } else {
        normalizedStack.push({
          vnode: currentVNode,
          recurseCount: 0
        });
      }
      const parentInstance = currentVNode.component && currentVNode.component.parent;
      currentVNode = parentInstance && parentInstance.vnode;
    }
    return normalizedStack;
  }
  function formatTrace(trace) {
    const logs = [];
    trace.forEach((entry, i) => {
      logs.push(...i === 0 ? [] : [`
`], ...formatTraceEntry(entry));
    });
    return logs;
  }
  function formatTraceEntry({ vnode, recurseCount }) {
    const postfix = recurseCount > 0 ? `... (${recurseCount} recursive calls)` : ``;
    const isRoot = vnode.component ? vnode.component.parent == null : false;
    const open = ` at <${formatComponentName(
      vnode.component,
      vnode.type,
      isRoot
    )}`;
    const close = `>` + postfix;
    return vnode.props ? [open, ...formatProps(vnode.props), close] : [open + close];
  }
  function formatProps(props) {
    const res = [];
    const keys = Object.keys(props);
    keys.slice(0, 3).forEach((key) => {
      res.push(...formatProp(key, props[key]));
    });
    if (keys.length > 3) {
      res.push(` ...`);
    }
    return res;
  }
  function formatProp(key, value, raw) {
    if (isString(value)) {
      value = JSON.stringify(value);
      return raw ? value : [`${key}=${value}`];
    } else if (typeof value === "number" || typeof value === "boolean" || value == null) {
      return raw ? value : [`${key}=${value}`];
    } else if (isRef2(value)) {
      value = formatProp(key, toRaw(value.value), true);
      return raw ? value : [`${key}=Ref<`, value, `>`];
    } else if (isFunction(value)) {
      return [`${key}=fn${value.name ? `<${value.name}>` : ``}`];
    } else {
      value = toRaw(value);
      return raw ? value : [`${key}=`, value];
    }
  }
  var ErrorTypeStrings$1 = {
    ["sp"]: "serverPrefetch hook",
    ["bc"]: "beforeCreate hook",
    ["c"]: "created hook",
    ["bm"]: "beforeMount hook",
    ["m"]: "mounted hook",
    ["bu"]: "beforeUpdate hook",
    ["u"]: "updated",
    ["bum"]: "beforeUnmount hook",
    ["um"]: "unmounted hook",
    ["a"]: "activated hook",
    ["da"]: "deactivated hook",
    ["ec"]: "errorCaptured hook",
    ["rtc"]: "renderTracked hook",
    ["rtg"]: "renderTriggered hook",
    [0]: "setup function",
    [1]: "render function",
    [2]: "watcher getter",
    [3]: "watcher callback",
    [4]: "watcher cleanup function",
    [5]: "native event handler",
    [6]: "component event handler",
    [7]: "vnode hook",
    [8]: "directive hook",
    [9]: "transition hook",
    [10]: "app errorHandler",
    [11]: "app warnHandler",
    [12]: "ref function",
    [13]: "async component loader",
    [14]: "scheduler flush",
    [15]: "component update",
    [16]: "app unmount cleanup function"
  };
  function callWithErrorHandling(fn2, instance, type, args) {
    try {
      return args ? fn2(...args) : fn2();
    } catch (err) {
      handleError(err, instance, type);
    }
  }
  function callWithAsyncErrorHandling(fn2, instance, type, args) {
    if (isFunction(fn2)) {
      const res = callWithErrorHandling(fn2, instance, type, args);
      if (res && isPromise(res)) {
        res.catch((err) => {
          handleError(err, instance, type);
        });
      }
      return res;
    }
    if (isArray(fn2)) {
      const values = [];
      for (let i = 0; i < fn2.length; i++) {
        values.push(callWithAsyncErrorHandling(fn2[i], instance, type, args));
      }
      return values;
    } else if (true) {
      warn$1(
        `Invalid value type passed to callWithAsyncErrorHandling(): ${typeof fn2}`
      );
    }
  }
  function handleError(err, instance, type, throwInDev = true) {
    const contextVNode = instance ? instance.vnode : null;
    const { errorHandler, throwUnhandledErrorInProduction } = instance && instance.appContext.config || EMPTY_OBJ;
    if (instance) {
      let cur = instance.parent;
      const exposedInstance = instance.proxy;
      const errorInfo = true ? ErrorTypeStrings$1[type] : `https://vuejs.org/error-reference/#runtime-${type}`;
      while (cur) {
        const errorCapturedHooks = cur.ec;
        if (errorCapturedHooks) {
          for (let i = 0; i < errorCapturedHooks.length; i++) {
            if (errorCapturedHooks[i](err, exposedInstance, errorInfo) === false) {
              return;
            }
          }
        }
        cur = cur.parent;
      }
      if (errorHandler) {
        pauseTracking();
        callWithErrorHandling(errorHandler, null, 10, [
          err,
          exposedInstance,
          errorInfo
        ]);
        resetTracking();
        return;
      }
    }
    logError(err, type, contextVNode, throwInDev, throwUnhandledErrorInProduction);
  }
  function logError(err, type, contextVNode, throwInDev = true, throwInProd = false) {
    if (true) {
      const info = ErrorTypeStrings$1[type];
      if (contextVNode) {
        pushWarningContext(contextVNode);
      }
      warn$1(`Unhandled error${info ? ` during execution of ${info}` : ``}`);
      if (contextVNode) {
        popWarningContext();
      }
      if (throwInDev) {
        throw err;
      } else {
        console.error(err);
      }
    } else if (throwInProd) {
      throw err;
    } else {
      console.error(err);
    }
  }
  var queue = [];
  var flushIndex = -1;
  var pendingPostFlushCbs = [];
  var activePostFlushCbs = null;
  var postFlushIndex = 0;
  var resolvedPromise = /* @__PURE__ */ Promise.resolve();
  var currentFlushPromise = null;
  var RECURSION_LIMIT = 100;
  function nextTick(fn2) {
    const p2 = currentFlushPromise || resolvedPromise;
    return fn2 ? p2.then(this ? fn2.bind(this) : fn2) : p2;
  }
  function findInsertionIndex(id) {
    let start2 = flushIndex + 1;
    let end2 = queue.length;
    while (start2 < end2) {
      const middle = start2 + end2 >>> 1;
      const middleJob = queue[middle];
      const middleJobId = getId(middleJob);
      if (middleJobId < id || middleJobId === id && middleJob.flags & 2) {
        start2 = middle + 1;
      } else {
        end2 = middle;
      }
    }
    return start2;
  }
  function queueJob(job) {
    if (!(job.flags & 1)) {
      const jobId = getId(job);
      const lastJob = queue[queue.length - 1];
      if (!lastJob || !(job.flags & 2) && jobId >= getId(lastJob)) {
        queue.push(job);
      } else {
        queue.splice(findInsertionIndex(jobId), 0, job);
      }
      job.flags |= 1;
      queueFlush();
    }
  }
  function queueFlush() {
    if (!currentFlushPromise) {
      currentFlushPromise = resolvedPromise.then(flushJobs);
    }
  }
  function queuePostFlushCb(cb) {
    if (!isArray(cb)) {
      if (activePostFlushCbs && cb.id === -1) {
        activePostFlushCbs.splice(postFlushIndex + 1, 0, cb);
      } else if (!(cb.flags & 1)) {
        pendingPostFlushCbs.push(cb);
        cb.flags |= 1;
      }
    } else {
      pendingPostFlushCbs.push(...cb);
    }
    queueFlush();
  }
  function flushPreFlushCbs(instance, seen, i = flushIndex + 1) {
    if (true) {
      seen = seen || /* @__PURE__ */ new Map();
    }
    for (; i < queue.length; i++) {
      const cb = queue[i];
      if (cb && cb.flags & 2) {
        if (instance && cb.id !== instance.uid) {
          continue;
        }
        if (checkRecursiveUpdates(seen, cb)) {
          continue;
        }
        queue.splice(i, 1);
        i--;
        if (cb.flags & 4) {
          cb.flags &= ~1;
        }
        cb();
        if (!(cb.flags & 4)) {
          cb.flags &= ~1;
        }
      }
    }
  }
  function flushPostFlushCbs(seen) {
    if (pendingPostFlushCbs.length) {
      const deduped = [...new Set(pendingPostFlushCbs)].sort(
        (a, b) => getId(a) - getId(b)
      );
      pendingPostFlushCbs.length = 0;
      if (activePostFlushCbs) {
        activePostFlushCbs.push(...deduped);
        return;
      }
      activePostFlushCbs = deduped;
      if (true) {
        seen = seen || /* @__PURE__ */ new Map();
      }
      for (postFlushIndex = 0; postFlushIndex < activePostFlushCbs.length; postFlushIndex++) {
        const cb = activePostFlushCbs[postFlushIndex];
        if (checkRecursiveUpdates(seen, cb)) {
          continue;
        }
        if (cb.flags & 4) {
          cb.flags &= ~1;
        }
        if (!(cb.flags & 8))
          cb();
        cb.flags &= ~1;
      }
      activePostFlushCbs = null;
      postFlushIndex = 0;
    }
  }
  var getId = (job) => job.id == null ? job.flags & 2 ? -1 : Infinity : job.id;
  function flushJobs(seen) {
    if (true) {
      seen = seen || /* @__PURE__ */ new Map();
    }
    const check = true ? (job) => checkRecursiveUpdates(seen, job) : NOOP;
    try {
      for (flushIndex = 0; flushIndex < queue.length; flushIndex++) {
        const job = queue[flushIndex];
        if (job && !(job.flags & 8)) {
          if (check(job)) {
            continue;
          }
          if (job.flags & 4) {
            job.flags &= ~1;
          }
          callWithErrorHandling(
            job,
            job.i,
            job.i ? 15 : 14
          );
          if (!(job.flags & 4)) {
            job.flags &= ~1;
          }
        }
      }
    } finally {
      for (; flushIndex < queue.length; flushIndex++) {
        const job = queue[flushIndex];
        if (job) {
          job.flags &= ~1;
        }
      }
      flushIndex = -1;
      queue.length = 0;
      flushPostFlushCbs(seen);
      currentFlushPromise = null;
      if (queue.length || pendingPostFlushCbs.length) {
        flushJobs(seen);
      }
    }
  }
  function checkRecursiveUpdates(seen, fn2) {
    const count = seen.get(fn2) || 0;
    if (count > RECURSION_LIMIT) {
      const instance = fn2.i;
      const componentName = instance && getComponentName(instance.type);
      handleError(
        `Maximum recursive updates exceeded${componentName ? ` in component <${componentName}>` : ``}. This means you have a reactive effect that is mutating its own dependencies and thus recursively triggering itself. Possible sources include component template, render function, updated hook or watcher source function.`,
        null,
        10
      );
      return true;
    }
    seen.set(fn2, count + 1);
    return false;
  }
  var isHmrUpdating = false;
  var hmrDirtyComponents = /* @__PURE__ */ new Map();
  if (true) {
    getGlobalThis().__VUE_HMR_RUNTIME__ = {
      createRecord: tryWrap(createRecord),
      rerender: tryWrap(rerender),
      reload: tryWrap(reload)
    };
  }
  var map = /* @__PURE__ */ new Map();
  function registerHMR(instance) {
    const id = instance.type.__hmrId;
    let record = map.get(id);
    if (!record) {
      createRecord(id, instance.type);
      record = map.get(id);
    }
    record.instances.add(instance);
  }
  function unregisterHMR(instance) {
    map.get(instance.type.__hmrId).instances.delete(instance);
  }
  function createRecord(id, initialDef) {
    if (map.has(id)) {
      return false;
    }
    map.set(id, {
      initialDef: normalizeClassComponent(initialDef),
      instances: /* @__PURE__ */ new Set()
    });
    return true;
  }
  function normalizeClassComponent(component) {
    return isClassComponent(component) ? component.__vccOpts : component;
  }
  function rerender(id, newRender) {
    const record = map.get(id);
    if (!record) {
      return;
    }
    record.initialDef.render = newRender;
    [...record.instances].forEach((instance) => {
      if (newRender) {
        instance.render = newRender;
        normalizeClassComponent(instance.type).render = newRender;
      }
      instance.renderCache = [];
      isHmrUpdating = true;
      instance.update();
      isHmrUpdating = false;
    });
  }
  function reload(id, newComp) {
    const record = map.get(id);
    if (!record)
      return;
    newComp = normalizeClassComponent(newComp);
    updateComponentDef(record.initialDef, newComp);
    const instances = [...record.instances];
    for (let i = 0; i < instances.length; i++) {
      const instance = instances[i];
      const oldComp = normalizeClassComponent(instance.type);
      let dirtyInstances = hmrDirtyComponents.get(oldComp);
      if (!dirtyInstances) {
        if (oldComp !== record.initialDef) {
          updateComponentDef(oldComp, newComp);
        }
        hmrDirtyComponents.set(oldComp, dirtyInstances = /* @__PURE__ */ new Set());
      }
      dirtyInstances.add(instance);
      instance.appContext.propsCache.delete(instance.type);
      instance.appContext.emitsCache.delete(instance.type);
      instance.appContext.optionsCache.delete(instance.type);
      if (instance.ceReload) {
        dirtyInstances.add(instance);
        instance.ceReload(newComp.styles);
        dirtyInstances.delete(instance);
      } else if (instance.parent) {
        queueJob(() => {
          isHmrUpdating = true;
          instance.parent.update();
          isHmrUpdating = false;
          dirtyInstances.delete(instance);
        });
      } else if (instance.appContext.reload) {
        instance.appContext.reload();
      } else if (typeof window !== "undefined") {
        window.location.reload();
      } else {
        console.warn(
          "[HMR] Root or manually mounted instance modified. Full reload required."
        );
      }
      if (instance.root.ce && instance !== instance.root) {
        instance.root.ce._removeChildStyle(oldComp);
      }
    }
    queuePostFlushCb(() => {
      hmrDirtyComponents.clear();
    });
  }
  function updateComponentDef(oldComp, newComp) {
    extend(oldComp, newComp);
    for (const key in oldComp) {
      if (key !== "__file" && !(key in newComp)) {
        delete oldComp[key];
      }
    }
  }
  function tryWrap(fn2) {
    return (id, arg) => {
      try {
        return fn2(id, arg);
      } catch (e) {
        console.error(e);
        console.warn(
          `[HMR] Something went wrong during Vue component hot-reload. Full reload required.`
        );
      }
    };
  }
  var devtools$1;
  var buffer = [];
  var devtoolsNotInstalled = false;
  function emit$1(event, ...args) {
    if (devtools$1) {
      devtools$1.emit(event, ...args);
    } else if (!devtoolsNotInstalled) {
      buffer.push({ event, args });
    }
  }
  function setDevtoolsHook$1(hook, target) {
    var _a, _b;
    devtools$1 = hook;
    if (devtools$1) {
      devtools$1.enabled = true;
      buffer.forEach(({ event, args }) => devtools$1.emit(event, ...args));
      buffer = [];
    } else if (typeof window !== "undefined" && window.HTMLElement && !((_b = (_a = window.navigator) == null ? void 0 : _a.userAgent) == null ? void 0 : _b.includes("jsdom"))) {
      const replay = target.__VUE_DEVTOOLS_HOOK_REPLAY__ = target.__VUE_DEVTOOLS_HOOK_REPLAY__ || [];
      replay.push((newHook) => {
        setDevtoolsHook$1(newHook, target);
      });
      setTimeout(() => {
        if (!devtools$1) {
          target.__VUE_DEVTOOLS_HOOK_REPLAY__ = null;
          devtoolsNotInstalled = true;
          buffer = [];
        }
      }, 3e3);
    } else {
      devtoolsNotInstalled = true;
      buffer = [];
    }
  }
  function devtoolsInitApp(app, version2) {
    emit$1("app:init", app, version2, {
      Fragment,
      Text,
      Comment,
      Static
    });
  }
  function devtoolsUnmountApp(app) {
    emit$1("app:unmount", app);
  }
  var devtoolsComponentAdded = /* @__PURE__ */ createDevtoolsComponentHook("component:added");
  var devtoolsComponentUpdated = /* @__PURE__ */ createDevtoolsComponentHook("component:updated");
  var _devtoolsComponentRemoved = /* @__PURE__ */ createDevtoolsComponentHook(
    "component:removed"
  );
  var devtoolsComponentRemoved = (component) => {
    if (devtools$1 && typeof devtools$1.cleanupBuffer === "function" && !devtools$1.cleanupBuffer(component)) {
      _devtoolsComponentRemoved(component);
    }
  };
  function createDevtoolsComponentHook(hook) {
    return (component) => {
      emit$1(
        hook,
        component.appContext.app,
        component.uid,
        component.parent ? component.parent.uid : void 0,
        component
      );
    };
  }
  var devtoolsPerfStart = /* @__PURE__ */ createDevtoolsPerformanceHook("perf:start");
  var devtoolsPerfEnd = /* @__PURE__ */ createDevtoolsPerformanceHook("perf:end");
  function createDevtoolsPerformanceHook(hook) {
    return (component, type, time) => {
      emit$1(hook, component.appContext.app, component.uid, component, type, time);
    };
  }
  function devtoolsComponentEmit(component, event, params) {
    emit$1(
      "component:emit",
      component.appContext.app,
      component,
      event,
      params
    );
  }
  var currentRenderingInstance = null;
  var currentScopeId = null;
  function setCurrentRenderingInstance(instance) {
    const prev = currentRenderingInstance;
    currentRenderingInstance = instance;
    currentScopeId = instance && instance.type.__scopeId || null;
    return prev;
  }
  function pushScopeId(id) {
    currentScopeId = id;
  }
  function popScopeId() {
    currentScopeId = null;
  }
  function withCtx(fn2, ctx = currentRenderingInstance, isNonScopedSlot) {
    if (!ctx)
      return fn2;
    if (fn2._n) {
      return fn2;
    }
    const renderFnWithContext = (...args) => {
      if (renderFnWithContext._d) {
        setBlockTracking(-1);
      }
      const prevInstance = setCurrentRenderingInstance(ctx);
      let res;
      try {
        res = fn2(...args);
      } finally {
        setCurrentRenderingInstance(prevInstance);
        if (renderFnWithContext._d) {
          setBlockTracking(1);
        }
      }
      if (true) {
        devtoolsComponentUpdated(ctx);
      }
      return res;
    };
    renderFnWithContext._n = true;
    renderFnWithContext._c = true;
    renderFnWithContext._d = true;
    return renderFnWithContext;
  }
  function validateDirectiveName(name) {
    if (isBuiltInDirective(name)) {
      warn$1("Do not use built-in directive ids as custom directive id: " + name);
    }
  }
  function withDirectives(vnode, directives) {
    if (currentRenderingInstance === null) {
      warn$1(`withDirectives can only be used inside render functions.`);
      return vnode;
    }
    const instance = getComponentPublicInstance(currentRenderingInstance);
    const bindings = vnode.dirs || (vnode.dirs = []);
    for (let i = 0; i < directives.length; i++) {
      let [dir, value, arg, modifiers = EMPTY_OBJ] = directives[i];
      if (dir) {
        if (isFunction(dir)) {
          dir = {
            mounted: dir,
            updated: dir
          };
        }
        if (dir.deep) {
          traverse(value);
        }
        bindings.push({
          dir,
          instance,
          value,
          oldValue: void 0,
          arg,
          modifiers
        });
      }
    }
    return vnode;
  }
  function invokeDirectiveHook(vnode, prevVNode, instance, name) {
    const bindings = vnode.dirs;
    const oldBindings = prevVNode && prevVNode.dirs;
    for (let i = 0; i < bindings.length; i++) {
      const binding = bindings[i];
      if (oldBindings) {
        binding.oldValue = oldBindings[i].value;
      }
      let hook = binding.dir[name];
      if (hook) {
        pauseTracking();
        callWithAsyncErrorHandling(hook, instance, 8, [
          vnode.el,
          binding,
          vnode,
          prevVNode
        ]);
        resetTracking();
      }
    }
  }
  var TeleportEndKey = Symbol("_vte");
  var isTeleport = (type) => type.__isTeleport;
  var leaveCbKey = Symbol("_leaveCb");
  var enterCbKey = Symbol("_enterCb");
  function setTransitionHooks(vnode, hooks) {
    if (vnode.shapeFlag & 6 && vnode.component) {
      vnode.transition = hooks;
      setTransitionHooks(vnode.component.subTree, hooks);
    } else if (vnode.shapeFlag & 128) {
      vnode.ssContent.transition = hooks.clone(vnode.ssContent);
      vnode.ssFallback.transition = hooks.clone(vnode.ssFallback);
    } else {
      vnode.transition = hooks;
    }
  }
  function markAsyncBoundary(instance) {
    instance.ids = [instance.ids[0] + instance.ids[2]++ + "-", 0, 0];
  }
  var knownTemplateRefs = /* @__PURE__ */ new WeakSet();
  function setRef(rawRef, oldRawRef, parentSuspense, vnode, isUnmount = false) {
    if (isArray(rawRef)) {
      rawRef.forEach(
        (r, i) => setRef(
          r,
          oldRawRef && (isArray(oldRawRef) ? oldRawRef[i] : oldRawRef),
          parentSuspense,
          vnode,
          isUnmount
        )
      );
      return;
    }
    if (isAsyncWrapper(vnode) && !isUnmount) {
      return;
    }
    const refValue = vnode.shapeFlag & 4 ? getComponentPublicInstance(vnode.component) : vnode.el;
    const value = isUnmount ? null : refValue;
    const { i: owner, r: ref3 } = rawRef;
    if (!owner) {
      warn$1(
        `Missing ref owner context. ref cannot be used on hoisted vnodes. A vnode with ref must be created inside the render function.`
      );
      return;
    }
    const oldRef = oldRawRef && oldRawRef.r;
    const refs = owner.refs === EMPTY_OBJ ? owner.refs = {} : owner.refs;
    const setupState = owner.setupState;
    const rawSetupState = toRaw(setupState);
    const canSetSetupRef = setupState === EMPTY_OBJ ? () => false : (key) => {
      if (true) {
        if (hasOwn(rawSetupState, key) && !isRef2(rawSetupState[key])) {
          warn$1(
            `Template ref "${key}" used on a non-ref value. It will not work in the production build.`
          );
        }
        if (knownTemplateRefs.has(rawSetupState[key])) {
          return false;
        }
      }
      return hasOwn(rawSetupState, key);
    };
    if (oldRef != null && oldRef !== ref3) {
      if (isString(oldRef)) {
        refs[oldRef] = null;
        if (canSetSetupRef(oldRef)) {
          setupState[oldRef] = null;
        }
      } else if (isRef2(oldRef)) {
        oldRef.value = null;
      }
    }
    if (isFunction(ref3)) {
      callWithErrorHandling(ref3, owner, 12, [value, refs]);
    } else {
      const _isString = isString(ref3);
      const _isRef = isRef2(ref3);
      if (_isString || _isRef) {
        const doSet = () => {
          if (rawRef.f) {
            const existing = _isString ? canSetSetupRef(ref3) ? setupState[ref3] : refs[ref3] : ref3.value;
            if (isUnmount) {
              isArray(existing) && remove(existing, refValue);
            } else {
              if (!isArray(existing)) {
                if (_isString) {
                  refs[ref3] = [refValue];
                  if (canSetSetupRef(ref3)) {
                    setupState[ref3] = refs[ref3];
                  }
                } else {
                  ref3.value = [refValue];
                  if (rawRef.k)
                    refs[rawRef.k] = ref3.value;
                }
              } else if (!existing.includes(refValue)) {
                existing.push(refValue);
              }
            }
          } else if (_isString) {
            refs[ref3] = value;
            if (canSetSetupRef(ref3)) {
              setupState[ref3] = value;
            }
          } else if (_isRef) {
            ref3.value = value;
            if (rawRef.k)
              refs[rawRef.k] = value;
          } else if (true) {
            warn$1("Invalid template ref type:", ref3, `(${typeof ref3})`);
          }
        };
        if (value) {
          doSet.id = -1;
          queuePostRenderEffect(doSet, parentSuspense);
        } else {
          doSet();
        }
      } else if (true) {
        warn$1("Invalid template ref type:", ref3, `(${typeof ref3})`);
      }
    }
  }
  var requestIdleCallback = getGlobalThis().requestIdleCallback || ((cb) => setTimeout(cb, 1));
  var cancelIdleCallback = getGlobalThis().cancelIdleCallback || ((id) => clearTimeout(id));
  var isAsyncWrapper = (i) => !!i.type.__asyncLoader;
  var isKeepAlive = (vnode) => vnode.type.__isKeepAlive;
  function onActivated(hook, target) {
    registerKeepAliveHook(hook, "a", target);
  }
  function onDeactivated(hook, target) {
    registerKeepAliveHook(hook, "da", target);
  }
  function registerKeepAliveHook(hook, type, target = currentInstance) {
    const wrappedHook = hook.__wdc || (hook.__wdc = () => {
      let current = target;
      while (current) {
        if (current.isDeactivated) {
          return;
        }
        current = current.parent;
      }
      return hook();
    });
    injectHook(type, wrappedHook, target);
    if (target) {
      let current = target.parent;
      while (current && current.parent) {
        if (isKeepAlive(current.parent.vnode)) {
          injectToKeepAliveRoot(wrappedHook, type, target, current);
        }
        current = current.parent;
      }
    }
  }
  function injectToKeepAliveRoot(hook, type, target, keepAliveRoot) {
    const injected = injectHook(
      type,
      hook,
      keepAliveRoot,
      true
    );
    onUnmounted(() => {
      remove(keepAliveRoot[type], injected);
    }, target);
  }
  function injectHook(type, hook, target = currentInstance, prepend = false) {
    if (target) {
      const hooks = target[type] || (target[type] = []);
      const wrappedHook = hook.__weh || (hook.__weh = (...args) => {
        pauseTracking();
        const reset = setCurrentInstance(target);
        const res = callWithAsyncErrorHandling(hook, target, type, args);
        reset();
        resetTracking();
        return res;
      });
      if (prepend) {
        hooks.unshift(wrappedHook);
      } else {
        hooks.push(wrappedHook);
      }
      return wrappedHook;
    } else if (true) {
      const apiName = toHandlerKey(ErrorTypeStrings$1[type].replace(/ hook$/, ""));
      warn$1(
        `${apiName} is called when there is no active component instance to be associated with. Lifecycle injection APIs can only be used during execution of setup(). If you are using async setup(), make sure to register lifecycle hooks before the first await statement.`
      );
    }
  }
  var createHook = (lifecycle) => (hook, target = currentInstance) => {
    if (!isInSSRComponentSetup || lifecycle === "sp") {
      injectHook(lifecycle, (...args) => hook(...args), target);
    }
  };
  var onBeforeMount = createHook("bm");
  var onMounted = createHook("m");
  var onBeforeUpdate = createHook(
    "bu"
  );
  var onUpdated = createHook("u");
  var onBeforeUnmount = createHook(
    "bum"
  );
  var onUnmounted = createHook("um");
  var onServerPrefetch = createHook(
    "sp"
  );
  var onRenderTriggered = createHook("rtg");
  var onRenderTracked = createHook("rtc");
  function onErrorCaptured(hook, target = currentInstance) {
    injectHook("ec", hook, target);
  }
  var NULL_DYNAMIC_COMPONENT = Symbol.for("v-ndc");
  function renderList(source, renderItem, cache, index) {
    let ret;
    const cached = cache && cache[index];
    const sourceIsArray = isArray(source);
    if (sourceIsArray || isString(source)) {
      const sourceIsReactiveArray = sourceIsArray && isReactive(source);
      let needsWrap = false;
      if (sourceIsReactiveArray) {
        needsWrap = !isShallow(source);
        source = shallowReadArray(source);
      }
      ret = new Array(source.length);
      for (let i = 0, l = source.length; i < l; i++) {
        ret[i] = renderItem(
          needsWrap ? toReactive(source[i]) : source[i],
          i,
          void 0,
          cached && cached[i]
        );
      }
    } else if (typeof source === "number") {
      if (!Number.isInteger(source)) {
        warn$1(`The v-for range expect an integer value but got ${source}.`);
      }
      ret = new Array(source);
      for (let i = 0; i < source; i++) {
        ret[i] = renderItem(i + 1, i, void 0, cached && cached[i]);
      }
    } else if (isObject(source)) {
      if (source[Symbol.iterator]) {
        ret = Array.from(
          source,
          (item, i) => renderItem(item, i, void 0, cached && cached[i])
        );
      } else {
        const keys = Object.keys(source);
        ret = new Array(keys.length);
        for (let i = 0, l = keys.length; i < l; i++) {
          const key = keys[i];
          ret[i] = renderItem(source[key], key, i, cached && cached[i]);
        }
      }
    } else {
      ret = [];
    }
    if (cache) {
      cache[index] = ret;
    }
    return ret;
  }
  var getPublicInstance = (i) => {
    if (!i)
      return null;
    if (isStatefulComponent(i))
      return getComponentPublicInstance(i);
    return getPublicInstance(i.parent);
  };
  var publicPropertiesMap = /* @__PURE__ */ extend(/* @__PURE__ */ Object.create(null), {
    $: (i) => i,
    $el: (i) => i.vnode.el,
    $data: (i) => i.data,
    $props: (i) => true ? shallowReadonly(i.props) : i.props,
    $attrs: (i) => true ? shallowReadonly(i.attrs) : i.attrs,
    $slots: (i) => true ? shallowReadonly(i.slots) : i.slots,
    $refs: (i) => true ? shallowReadonly(i.refs) : i.refs,
    $parent: (i) => getPublicInstance(i.parent),
    $root: (i) => getPublicInstance(i.root),
    $host: (i) => i.ce,
    $emit: (i) => i.emit,
    $options: (i) => true ? resolveMergedOptions(i) : i.type,
    $forceUpdate: (i) => i.f || (i.f = () => {
      queueJob(i.update);
    }),
    $nextTick: (i) => i.n || (i.n = nextTick.bind(i.proxy)),
    $watch: (i) => true ? instanceWatch.bind(i) : NOOP
  });
  var isReservedPrefix = (key) => key === "_" || key === "$";
  var hasSetupBinding = (state, key) => state !== EMPTY_OBJ && !state.__isScriptSetup && hasOwn(state, key);
  var PublicInstanceProxyHandlers = {
    get({ _: instance }, key) {
      if (key === "__v_skip") {
        return true;
      }
      const { ctx, setupState, data, props, accessCache, type, appContext } = instance;
      if (key === "__isVue") {
        return true;
      }
      let normalizedProps;
      if (key[0] !== "$") {
        const n = accessCache[key];
        if (n !== void 0) {
          switch (n) {
            case 1:
              return setupState[key];
            case 2:
              return data[key];
            case 4:
              return ctx[key];
            case 3:
              return props[key];
          }
        } else if (hasSetupBinding(setupState, key)) {
          accessCache[key] = 1;
          return setupState[key];
        } else if (data !== EMPTY_OBJ && hasOwn(data, key)) {
          accessCache[key] = 2;
          return data[key];
        } else if ((normalizedProps = instance.propsOptions[0]) && hasOwn(normalizedProps, key)) {
          accessCache[key] = 3;
          return props[key];
        } else if (ctx !== EMPTY_OBJ && hasOwn(ctx, key)) {
          accessCache[key] = 4;
          return ctx[key];
        } else if (shouldCacheAccess) {
          accessCache[key] = 0;
        }
      }
      const publicGetter = publicPropertiesMap[key];
      let cssModule, globalProperties;
      if (publicGetter) {
        if (key === "$attrs") {
          track(instance.attrs, "get", "");
          markAttrsAccessed();
        } else if (key === "$slots") {
          track(instance, "get", key);
        }
        return publicGetter(instance);
      } else if ((cssModule = type.__cssModules) && (cssModule = cssModule[key])) {
        return cssModule;
      } else if (ctx !== EMPTY_OBJ && hasOwn(ctx, key)) {
        accessCache[key] = 4;
        return ctx[key];
      } else if (globalProperties = appContext.config.globalProperties, hasOwn(globalProperties, key)) {
        {
          return globalProperties[key];
        }
      } else if (currentRenderingInstance && (!isString(key) || key.indexOf("__v") !== 0)) {
        if (data !== EMPTY_OBJ && isReservedPrefix(key[0]) && hasOwn(data, key)) {
          warn$1(
            `Property ${JSON.stringify(
              key
            )} must be accessed via $data because it starts with a reserved character ("$" or "_") and is not proxied on the render context.`
          );
        } else if (instance === currentRenderingInstance) {
          warn$1(
            `Property ${JSON.stringify(key)} was accessed during render but is not defined on instance.`
          );
        }
      }
    },
    set({ _: instance }, key, value) {
      const { data, setupState, ctx } = instance;
      if (hasSetupBinding(setupState, key)) {
        setupState[key] = value;
        return true;
      } else if (setupState.__isScriptSetup && hasOwn(setupState, key)) {
        warn$1(`Cannot mutate <script setup> binding "${key}" from Options API.`);
        return false;
      } else if (data !== EMPTY_OBJ && hasOwn(data, key)) {
        data[key] = value;
        return true;
      } else if (hasOwn(instance.props, key)) {
        warn$1(`Attempting to mutate prop "${key}". Props are readonly.`);
        return false;
      }
      if (key[0] === "$" && key.slice(1) in instance) {
        warn$1(
          `Attempting to mutate public property "${key}". Properties starting with $ are reserved and readonly.`
        );
        return false;
      } else {
        if (key in instance.appContext.config.globalProperties) {
          Object.defineProperty(ctx, key, {
            enumerable: true,
            configurable: true,
            value
          });
        } else {
          ctx[key] = value;
        }
      }
      return true;
    },
    has({
      _: { data, setupState, accessCache, ctx, appContext, propsOptions }
    }, key) {
      let normalizedProps;
      return !!accessCache[key] || data !== EMPTY_OBJ && hasOwn(data, key) || hasSetupBinding(setupState, key) || (normalizedProps = propsOptions[0]) && hasOwn(normalizedProps, key) || hasOwn(ctx, key) || hasOwn(publicPropertiesMap, key) || hasOwn(appContext.config.globalProperties, key);
    },
    defineProperty(target, key, descriptor) {
      if (descriptor.get != null) {
        target._.accessCache[key] = 0;
      } else if (hasOwn(descriptor, "value")) {
        this.set(target, key, descriptor.value, null);
      }
      return Reflect.defineProperty(target, key, descriptor);
    }
  };
  if (true) {
    PublicInstanceProxyHandlers.ownKeys = (target) => {
      warn$1(
        `Avoid app logic that relies on enumerating keys on a component instance. The keys will be empty in production mode to avoid performance overhead.`
      );
      return Reflect.ownKeys(target);
    };
  }
  function createDevRenderContext(instance) {
    const target = {};
    Object.defineProperty(target, `_`, {
      configurable: true,
      enumerable: false,
      get: () => instance
    });
    Object.keys(publicPropertiesMap).forEach((key) => {
      Object.defineProperty(target, key, {
        configurable: true,
        enumerable: false,
        get: () => publicPropertiesMap[key](instance),
        set: NOOP
      });
    });
    return target;
  }
  function exposePropsOnRenderContext(instance) {
    const {
      ctx,
      propsOptions: [propsOptions]
    } = instance;
    if (propsOptions) {
      Object.keys(propsOptions).forEach((key) => {
        Object.defineProperty(ctx, key, {
          enumerable: true,
          configurable: true,
          get: () => instance.props[key],
          set: NOOP
        });
      });
    }
  }
  function exposeSetupStateOnRenderContext(instance) {
    const { ctx, setupState } = instance;
    Object.keys(toRaw(setupState)).forEach((key) => {
      if (!setupState.__isScriptSetup) {
        if (isReservedPrefix(key[0])) {
          warn$1(
            `setup() return property ${JSON.stringify(
              key
            )} should not start with "$" or "_" which are reserved prefixes for Vue internals.`
          );
          return;
        }
        Object.defineProperty(ctx, key, {
          enumerable: true,
          configurable: true,
          get: () => setupState[key],
          set: NOOP
        });
      }
    });
  }
  function normalizePropsOrEmits(props) {
    return isArray(props) ? props.reduce(
      (normalized, p2) => (normalized[p2] = null, normalized),
      {}
    ) : props;
  }
  function createDuplicateChecker() {
    const cache = /* @__PURE__ */ Object.create(null);
    return (type, key) => {
      if (cache[key]) {
        warn$1(`${type} property "${key}" is already defined in ${cache[key]}.`);
      } else {
        cache[key] = type;
      }
    };
  }
  var shouldCacheAccess = true;
  function applyOptions(instance) {
    const options = resolveMergedOptions(instance);
    const publicThis = instance.proxy;
    const ctx = instance.ctx;
    shouldCacheAccess = false;
    if (options.beforeCreate) {
      callHook(options.beforeCreate, instance, "bc");
    }
    const {
      data: dataOptions,
      computed: computedOptions,
      methods,
      watch: watchOptions,
      provide: provideOptions,
      inject: injectOptions,
      created,
      beforeMount,
      mounted,
      beforeUpdate,
      updated,
      activated,
      deactivated,
      beforeDestroy,
      beforeUnmount,
      destroyed,
      unmounted,
      render: render8,
      renderTracked,
      renderTriggered,
      errorCaptured,
      serverPrefetch,
      expose,
      inheritAttrs,
      components,
      directives,
      filters
    } = options;
    const checkDuplicateProperties = true ? createDuplicateChecker() : null;
    if (true) {
      const [propsOptions] = instance.propsOptions;
      if (propsOptions) {
        for (const key in propsOptions) {
          checkDuplicateProperties("Props", key);
        }
      }
    }
    if (injectOptions) {
      resolveInjections(injectOptions, ctx, checkDuplicateProperties);
    }
    if (methods) {
      for (const key in methods) {
        const methodHandler = methods[key];
        if (isFunction(methodHandler)) {
          if (true) {
            Object.defineProperty(ctx, key, {
              value: methodHandler.bind(publicThis),
              configurable: true,
              enumerable: true,
              writable: true
            });
          } else {
            ctx[key] = methodHandler.bind(publicThis);
          }
          if (true) {
            checkDuplicateProperties("Methods", key);
          }
        } else if (true) {
          warn$1(
            `Method "${key}" has type "${typeof methodHandler}" in the component definition. Did you reference the function correctly?`
          );
        }
      }
    }
    if (dataOptions) {
      if (!isFunction(dataOptions)) {
        warn$1(
          `The data option must be a function. Plain object usage is no longer supported.`
        );
      }
      const data = dataOptions.call(publicThis, publicThis);
      if (isPromise(data)) {
        warn$1(
          `data() returned a Promise - note data() cannot be async; If you intend to perform data fetching before component renders, use async setup() + <Suspense>.`
        );
      }
      if (!isObject(data)) {
        warn$1(`data() should return an object.`);
      } else {
        instance.data = reactive(data);
        if (true) {
          for (const key in data) {
            checkDuplicateProperties("Data", key);
            if (!isReservedPrefix(key[0])) {
              Object.defineProperty(ctx, key, {
                configurable: true,
                enumerable: true,
                get: () => data[key],
                set: NOOP
              });
            }
          }
        }
      }
    }
    shouldCacheAccess = true;
    if (computedOptions) {
      for (const key in computedOptions) {
        const opt = computedOptions[key];
        const get2 = isFunction(opt) ? opt.bind(publicThis, publicThis) : isFunction(opt.get) ? opt.get.bind(publicThis, publicThis) : NOOP;
        if (get2 === NOOP) {
          warn$1(`Computed property "${key}" has no getter.`);
        }
        const set2 = !isFunction(opt) && isFunction(opt.set) ? opt.set.bind(publicThis) : true ? () => {
          warn$1(
            `Write operation failed: computed property "${key}" is readonly.`
          );
        } : NOOP;
        const c = computed2({
          get: get2,
          set: set2
        });
        Object.defineProperty(ctx, key, {
          enumerable: true,
          configurable: true,
          get: () => c.value,
          set: (v) => c.value = v
        });
        if (true) {
          checkDuplicateProperties("Computed", key);
        }
      }
    }
    if (watchOptions) {
      for (const key in watchOptions) {
        createWatcher(watchOptions[key], ctx, publicThis, key);
      }
    }
    if (provideOptions) {
      const provides = isFunction(provideOptions) ? provideOptions.call(publicThis) : provideOptions;
      Reflect.ownKeys(provides).forEach((key) => {
        provide(key, provides[key]);
      });
    }
    if (created) {
      callHook(created, instance, "c");
    }
    function registerLifecycleHook(register, hook) {
      if (isArray(hook)) {
        hook.forEach((_hook) => register(_hook.bind(publicThis)));
      } else if (hook) {
        register(hook.bind(publicThis));
      }
    }
    registerLifecycleHook(onBeforeMount, beforeMount);
    registerLifecycleHook(onMounted, mounted);
    registerLifecycleHook(onBeforeUpdate, beforeUpdate);
    registerLifecycleHook(onUpdated, updated);
    registerLifecycleHook(onActivated, activated);
    registerLifecycleHook(onDeactivated, deactivated);
    registerLifecycleHook(onErrorCaptured, errorCaptured);
    registerLifecycleHook(onRenderTracked, renderTracked);
    registerLifecycleHook(onRenderTriggered, renderTriggered);
    registerLifecycleHook(onBeforeUnmount, beforeUnmount);
    registerLifecycleHook(onUnmounted, unmounted);
    registerLifecycleHook(onServerPrefetch, serverPrefetch);
    if (isArray(expose)) {
      if (expose.length) {
        const exposed = instance.exposed || (instance.exposed = {});
        expose.forEach((key) => {
          Object.defineProperty(exposed, key, {
            get: () => publicThis[key],
            set: (val) => publicThis[key] = val
          });
        });
      } else if (!instance.exposed) {
        instance.exposed = {};
      }
    }
    if (render8 && instance.render === NOOP) {
      instance.render = render8;
    }
    if (inheritAttrs != null) {
      instance.inheritAttrs = inheritAttrs;
    }
    if (components)
      instance.components = components;
    if (directives)
      instance.directives = directives;
    if (serverPrefetch) {
      markAsyncBoundary(instance);
    }
  }
  function resolveInjections(injectOptions, ctx, checkDuplicateProperties = NOOP) {
    if (isArray(injectOptions)) {
      injectOptions = normalizeInject(injectOptions);
    }
    for (const key in injectOptions) {
      const opt = injectOptions[key];
      let injected;
      if (isObject(opt)) {
        if ("default" in opt) {
          injected = inject(
            opt.from || key,
            opt.default,
            true
          );
        } else {
          injected = inject(opt.from || key);
        }
      } else {
        injected = inject(opt);
      }
      if (isRef2(injected)) {
        Object.defineProperty(ctx, key, {
          enumerable: true,
          configurable: true,
          get: () => injected.value,
          set: (v) => injected.value = v
        });
      } else {
        ctx[key] = injected;
      }
      if (true) {
        checkDuplicateProperties("Inject", key);
      }
    }
  }
  function callHook(hook, instance, type) {
    callWithAsyncErrorHandling(
      isArray(hook) ? hook.map((h3) => h3.bind(instance.proxy)) : hook.bind(instance.proxy),
      instance,
      type
    );
  }
  function createWatcher(raw, ctx, publicThis, key) {
    let getter = key.includes(".") ? createPathGetter(publicThis, key) : () => publicThis[key];
    if (isString(raw)) {
      const handler = ctx[raw];
      if (isFunction(handler)) {
        {
          watch2(getter, handler);
        }
      } else if (true) {
        warn$1(`Invalid watch handler specified by key "${raw}"`, handler);
      }
    } else if (isFunction(raw)) {
      {
        watch2(getter, raw.bind(publicThis));
      }
    } else if (isObject(raw)) {
      if (isArray(raw)) {
        raw.forEach((r) => createWatcher(r, ctx, publicThis, key));
      } else {
        const handler = isFunction(raw.handler) ? raw.handler.bind(publicThis) : ctx[raw.handler];
        if (isFunction(handler)) {
          watch2(getter, handler, raw);
        } else if (true) {
          warn$1(`Invalid watch handler specified by key "${raw.handler}"`, handler);
        }
      }
    } else if (true) {
      warn$1(`Invalid watch option: "${key}"`, raw);
    }
  }
  function resolveMergedOptions(instance) {
    const base = instance.type;
    const { mixins, extends: extendsOptions } = base;
    const {
      mixins: globalMixins,
      optionsCache: cache,
      config: { optionMergeStrategies }
    } = instance.appContext;
    const cached = cache.get(base);
    let resolved;
    if (cached) {
      resolved = cached;
    } else if (!globalMixins.length && !mixins && !extendsOptions) {
      {
        resolved = base;
      }
    } else {
      resolved = {};
      if (globalMixins.length) {
        globalMixins.forEach(
          (m) => mergeOptions(resolved, m, optionMergeStrategies, true)
        );
      }
      mergeOptions(resolved, base, optionMergeStrategies);
    }
    if (isObject(base)) {
      cache.set(base, resolved);
    }
    return resolved;
  }
  function mergeOptions(to, from, strats, asMixin = false) {
    const { mixins, extends: extendsOptions } = from;
    if (extendsOptions) {
      mergeOptions(to, extendsOptions, strats, true);
    }
    if (mixins) {
      mixins.forEach(
        (m) => mergeOptions(to, m, strats, true)
      );
    }
    for (const key in from) {
      if (asMixin && key === "expose") {
        warn$1(
          `"expose" option is ignored when declared in mixins or extends. It should only be declared in the base component itself.`
        );
      } else {
        const strat = internalOptionMergeStrats[key] || strats && strats[key];
        to[key] = strat ? strat(to[key], from[key]) : from[key];
      }
    }
    return to;
  }
  var internalOptionMergeStrats = {
    data: mergeDataFn,
    props: mergeEmitsOrPropsOptions,
    emits: mergeEmitsOrPropsOptions,
    methods: mergeObjectOptions,
    computed: mergeObjectOptions,
    beforeCreate: mergeAsArray,
    created: mergeAsArray,
    beforeMount: mergeAsArray,
    mounted: mergeAsArray,
    beforeUpdate: mergeAsArray,
    updated: mergeAsArray,
    beforeDestroy: mergeAsArray,
    beforeUnmount: mergeAsArray,
    destroyed: mergeAsArray,
    unmounted: mergeAsArray,
    activated: mergeAsArray,
    deactivated: mergeAsArray,
    errorCaptured: mergeAsArray,
    serverPrefetch: mergeAsArray,
    components: mergeObjectOptions,
    directives: mergeObjectOptions,
    watch: mergeWatchOptions,
    provide: mergeDataFn,
    inject: mergeInject
  };
  function mergeDataFn(to, from) {
    if (!from) {
      return to;
    }
    if (!to) {
      return from;
    }
    return function mergedDataFn() {
      return extend(
        isFunction(to) ? to.call(this, this) : to,
        isFunction(from) ? from.call(this, this) : from
      );
    };
  }
  function mergeInject(to, from) {
    return mergeObjectOptions(normalizeInject(to), normalizeInject(from));
  }
  function normalizeInject(raw) {
    if (isArray(raw)) {
      const res = {};
      for (let i = 0; i < raw.length; i++) {
        res[raw[i]] = raw[i];
      }
      return res;
    }
    return raw;
  }
  function mergeAsArray(to, from) {
    return to ? [...new Set([].concat(to, from))] : from;
  }
  function mergeObjectOptions(to, from) {
    return to ? extend(/* @__PURE__ */ Object.create(null), to, from) : from;
  }
  function mergeEmitsOrPropsOptions(to, from) {
    if (to) {
      if (isArray(to) && isArray(from)) {
        return [.../* @__PURE__ */ new Set([...to, ...from])];
      }
      return extend(
        /* @__PURE__ */ Object.create(null),
        normalizePropsOrEmits(to),
        normalizePropsOrEmits(from != null ? from : {})
      );
    } else {
      return from;
    }
  }
  function mergeWatchOptions(to, from) {
    if (!to)
      return from;
    if (!from)
      return to;
    const merged = extend(/* @__PURE__ */ Object.create(null), to);
    for (const key in from) {
      merged[key] = mergeAsArray(to[key], from[key]);
    }
    return merged;
  }
  function createAppContext() {
    return {
      app: null,
      config: {
        isNativeTag: NO,
        performance: false,
        globalProperties: {},
        optionMergeStrategies: {},
        errorHandler: void 0,
        warnHandler: void 0,
        compilerOptions: {}
      },
      mixins: [],
      components: {},
      directives: {},
      provides: /* @__PURE__ */ Object.create(null),
      optionsCache: /* @__PURE__ */ new WeakMap(),
      propsCache: /* @__PURE__ */ new WeakMap(),
      emitsCache: /* @__PURE__ */ new WeakMap()
    };
  }
  var uid$1 = 0;
  function createAppAPI(render8, hydrate) {
    return function createApp2(rootComponent, rootProps = null) {
      if (!isFunction(rootComponent)) {
        rootComponent = extend({}, rootComponent);
      }
      if (rootProps != null && !isObject(rootProps)) {
        warn$1(`root props passed to app.mount() must be an object.`);
        rootProps = null;
      }
      const context = createAppContext();
      const installedPlugins = /* @__PURE__ */ new WeakSet();
      const pluginCleanupFns = [];
      let isMounted = false;
      const app = context.app = {
        _uid: uid$1++,
        _component: rootComponent,
        _props: rootProps,
        _container: null,
        _context: context,
        _instance: null,
        version,
        get config() {
          return context.config;
        },
        set config(v) {
          if (true) {
            warn$1(
              `app.config cannot be replaced. Modify individual options instead.`
            );
          }
        },
        use(plugin, ...options) {
          if (installedPlugins.has(plugin)) {
            warn$1(`Plugin has already been applied to target app.`);
          } else if (plugin && isFunction(plugin.install)) {
            installedPlugins.add(plugin);
            plugin.install(app, ...options);
          } else if (isFunction(plugin)) {
            installedPlugins.add(plugin);
            plugin(app, ...options);
          } else if (true) {
            warn$1(
              `A plugin must either be a function or an object with an "install" function.`
            );
          }
          return app;
        },
        mixin(mixin) {
          if (true) {
            if (!context.mixins.includes(mixin)) {
              context.mixins.push(mixin);
            } else if (true) {
              warn$1(
                "Mixin has already been applied to target app" + (mixin.name ? `: ${mixin.name}` : "")
              );
            }
          } else if (true) {
            warn$1("Mixins are only available in builds supporting Options API");
          }
          return app;
        },
        component(name, component) {
          if (true) {
            validateComponentName(name, context.config);
          }
          if (!component) {
            return context.components[name];
          }
          if (context.components[name]) {
            warn$1(`Component "${name}" has already been registered in target app.`);
          }
          context.components[name] = component;
          return app;
        },
        directive(name, directive) {
          if (true) {
            validateDirectiveName(name);
          }
          if (!directive) {
            return context.directives[name];
          }
          if (context.directives[name]) {
            warn$1(`Directive "${name}" has already been registered in target app.`);
          }
          context.directives[name] = directive;
          return app;
        },
        mount(rootContainer, isHydrate, namespace) {
          if (!isMounted) {
            if (rootContainer.__vue_app__) {
              warn$1(
                `There is already an app instance mounted on the host container.
 If you want to mount another app on the same host container, you need to unmount the previous app by calling \`app.unmount()\` first.`
              );
            }
            const vnode = app._ceVNode || createVNode(rootComponent, rootProps);
            vnode.appContext = context;
            if (namespace === true) {
              namespace = "svg";
            } else if (namespace === false) {
              namespace = void 0;
            }
            if (true) {
              context.reload = () => {
                render8(
                  cloneVNode(vnode),
                  rootContainer,
                  namespace
                );
              };
            }
            if (isHydrate && hydrate) {
              hydrate(vnode, rootContainer);
            } else {
              render8(vnode, rootContainer, namespace);
            }
            isMounted = true;
            app._container = rootContainer;
            rootContainer.__vue_app__ = app;
            if (true) {
              app._instance = vnode.component;
              devtoolsInitApp(app, version);
            }
            return getComponentPublicInstance(vnode.component);
          } else if (true) {
            warn$1(
              `App has already been mounted.
If you want to remount the same app, move your app creation logic into a factory function and create fresh app instances for each mount - e.g. \`const createMyApp = () => createApp(App)\``
            );
          }
        },
        onUnmount(cleanupFn) {
          if (typeof cleanupFn !== "function") {
            warn$1(
              `Expected function as first argument to app.onUnmount(), but got ${typeof cleanupFn}`
            );
          }
          pluginCleanupFns.push(cleanupFn);
        },
        unmount() {
          if (isMounted) {
            callWithAsyncErrorHandling(
              pluginCleanupFns,
              app._instance,
              16
            );
            render8(null, app._container);
            if (true) {
              app._instance = null;
              devtoolsUnmountApp(app);
            }
            delete app._container.__vue_app__;
          } else if (true) {
            warn$1(`Cannot unmount an app that is not mounted.`);
          }
        },
        provide(key, value) {
          if (key in context.provides) {
            warn$1(
              `App already provides property with key "${String(key)}". It will be overwritten with the new value.`
            );
          }
          context.provides[key] = value;
          return app;
        },
        runWithContext(fn2) {
          const lastApp = currentApp;
          currentApp = app;
          try {
            return fn2();
          } finally {
            currentApp = lastApp;
          }
        }
      };
      return app;
    };
  }
  var currentApp = null;
  function provide(key, value) {
    if (!currentInstance) {
      if (true) {
        warn$1(`provide() can only be used inside setup().`);
      }
    } else {
      let provides = currentInstance.provides;
      const parentProvides = currentInstance.parent && currentInstance.parent.provides;
      if (parentProvides === provides) {
        provides = currentInstance.provides = Object.create(parentProvides);
      }
      provides[key] = value;
    }
  }
  function inject(key, defaultValue, treatDefaultAsFactory = false) {
    const instance = currentInstance || currentRenderingInstance;
    if (instance || currentApp) {
      const provides = currentApp ? currentApp._context.provides : instance ? instance.parent == null ? instance.vnode.appContext && instance.vnode.appContext.provides : instance.parent.provides : void 0;
      if (provides && key in provides) {
        return provides[key];
      } else if (arguments.length > 1) {
        return treatDefaultAsFactory && isFunction(defaultValue) ? defaultValue.call(instance && instance.proxy) : defaultValue;
      } else if (true) {
        warn$1(`injection "${String(key)}" not found.`);
      }
    } else if (true) {
      warn$1(`inject() can only be used inside setup() or functional components.`);
    }
  }
  var internalObjectProto = {};
  var createInternalObject = () => Object.create(internalObjectProto);
  var isInternalObject = (obj) => Object.getPrototypeOf(obj) === internalObjectProto;
  function initProps(instance, rawProps, isStateful, isSSR = false) {
    const props = {};
    const attrs = createInternalObject();
    instance.propsDefaults = /* @__PURE__ */ Object.create(null);
    setFullProps(instance, rawProps, props, attrs);
    for (const key in instance.propsOptions[0]) {
      if (!(key in props)) {
        props[key] = void 0;
      }
    }
    if (true) {
      validateProps(rawProps || {}, props, instance);
    }
    if (isStateful) {
      instance.props = isSSR ? props : shallowReactive(props);
    } else {
      if (!instance.type.props) {
        instance.props = attrs;
      } else {
        instance.props = props;
      }
    }
    instance.attrs = attrs;
  }
  function isInHmrContext(instance) {
    while (instance) {
      if (instance.type.__hmrId)
        return true;
      instance = instance.parent;
    }
  }
  function updateProps(instance, rawProps, rawPrevProps, optimized) {
    const {
      props,
      attrs,
      vnode: { patchFlag }
    } = instance;
    const rawCurrentProps = toRaw(props);
    const [options] = instance.propsOptions;
    let hasAttrsChanged = false;
    if (!isInHmrContext(instance) && (optimized || patchFlag > 0) && !(patchFlag & 16)) {
      if (patchFlag & 8) {
        const propsToUpdate = instance.vnode.dynamicProps;
        for (let i = 0; i < propsToUpdate.length; i++) {
          let key = propsToUpdate[i];
          if (isEmitListener(instance.emitsOptions, key)) {
            continue;
          }
          const value = rawProps[key];
          if (options) {
            if (hasOwn(attrs, key)) {
              if (value !== attrs[key]) {
                attrs[key] = value;
                hasAttrsChanged = true;
              }
            } else {
              const camelizedKey = camelize(key);
              props[camelizedKey] = resolvePropValue(
                options,
                rawCurrentProps,
                camelizedKey,
                value,
                instance,
                false
              );
            }
          } else {
            if (value !== attrs[key]) {
              attrs[key] = value;
              hasAttrsChanged = true;
            }
          }
        }
      }
    } else {
      if (setFullProps(instance, rawProps, props, attrs)) {
        hasAttrsChanged = true;
      }
      let kebabKey;
      for (const key in rawCurrentProps) {
        if (!rawProps || !hasOwn(rawProps, key) && ((kebabKey = hyphenate(key)) === key || !hasOwn(rawProps, kebabKey))) {
          if (options) {
            if (rawPrevProps && (rawPrevProps[key] !== void 0 || rawPrevProps[kebabKey] !== void 0)) {
              props[key] = resolvePropValue(
                options,
                rawCurrentProps,
                key,
                void 0,
                instance,
                true
              );
            }
          } else {
            delete props[key];
          }
        }
      }
      if (attrs !== rawCurrentProps) {
        for (const key in attrs) {
          if (!rawProps || !hasOwn(rawProps, key) && true) {
            delete attrs[key];
            hasAttrsChanged = true;
          }
        }
      }
    }
    if (hasAttrsChanged) {
      trigger(instance.attrs, "set", "");
    }
    if (true) {
      validateProps(rawProps || {}, props, instance);
    }
  }
  function setFullProps(instance, rawProps, props, attrs) {
    const [options, needCastKeys] = instance.propsOptions;
    let hasAttrsChanged = false;
    let rawCastValues;
    if (rawProps) {
      for (let key in rawProps) {
        if (isReservedProp(key)) {
          continue;
        }
        const value = rawProps[key];
        let camelKey;
        if (options && hasOwn(options, camelKey = camelize(key))) {
          if (!needCastKeys || !needCastKeys.includes(camelKey)) {
            props[camelKey] = value;
          } else {
            (rawCastValues || (rawCastValues = {}))[camelKey] = value;
          }
        } else if (!isEmitListener(instance.emitsOptions, key)) {
          if (!(key in attrs) || value !== attrs[key]) {
            attrs[key] = value;
            hasAttrsChanged = true;
          }
        }
      }
    }
    if (needCastKeys) {
      const rawCurrentProps = toRaw(props);
      const castValues = rawCastValues || EMPTY_OBJ;
      for (let i = 0; i < needCastKeys.length; i++) {
        const key = needCastKeys[i];
        props[key] = resolvePropValue(
          options,
          rawCurrentProps,
          key,
          castValues[key],
          instance,
          !hasOwn(castValues, key)
        );
      }
    }
    return hasAttrsChanged;
  }
  function resolvePropValue(options, props, key, value, instance, isAbsent) {
    const opt = options[key];
    if (opt != null) {
      const hasDefault = hasOwn(opt, "default");
      if (hasDefault && value === void 0) {
        const defaultValue = opt.default;
        if (opt.type !== Function && !opt.skipFactory && isFunction(defaultValue)) {
          const { propsDefaults } = instance;
          if (key in propsDefaults) {
            value = propsDefaults[key];
          } else {
            const reset = setCurrentInstance(instance);
            value = propsDefaults[key] = defaultValue.call(
              null,
              props
            );
            reset();
          }
        } else {
          value = defaultValue;
        }
        if (instance.ce) {
          instance.ce._setProp(key, value);
        }
      }
      if (opt[0]) {
        if (isAbsent && !hasDefault) {
          value = false;
        } else if (opt[1] && (value === "" || value === hyphenate(key))) {
          value = true;
        }
      }
    }
    return value;
  }
  var mixinPropsCache = /* @__PURE__ */ new WeakMap();
  function normalizePropsOptions(comp, appContext, asMixin = false) {
    const cache = asMixin ? mixinPropsCache : appContext.propsCache;
    const cached = cache.get(comp);
    if (cached) {
      return cached;
    }
    const raw = comp.props;
    const normalized = {};
    const needCastKeys = [];
    let hasExtends = false;
    if (!isFunction(comp)) {
      const extendProps = (raw2) => {
        hasExtends = true;
        const [props, keys] = normalizePropsOptions(raw2, appContext, true);
        extend(normalized, props);
        if (keys)
          needCastKeys.push(...keys);
      };
      if (!asMixin && appContext.mixins.length) {
        appContext.mixins.forEach(extendProps);
      }
      if (comp.extends) {
        extendProps(comp.extends);
      }
      if (comp.mixins) {
        comp.mixins.forEach(extendProps);
      }
    }
    if (!raw && !hasExtends) {
      if (isObject(comp)) {
        cache.set(comp, EMPTY_ARR);
      }
      return EMPTY_ARR;
    }
    if (isArray(raw)) {
      for (let i = 0; i < raw.length; i++) {
        if (!isString(raw[i])) {
          warn$1(`props must be strings when using array syntax.`, raw[i]);
        }
        const normalizedKey = camelize(raw[i]);
        if (validatePropName(normalizedKey)) {
          normalized[normalizedKey] = EMPTY_OBJ;
        }
      }
    } else if (raw) {
      if (!isObject(raw)) {
        warn$1(`invalid props options`, raw);
      }
      for (const key in raw) {
        const normalizedKey = camelize(key);
        if (validatePropName(normalizedKey)) {
          const opt = raw[key];
          const prop = normalized[normalizedKey] = isArray(opt) || isFunction(opt) ? { type: opt } : extend({}, opt);
          const propType = prop.type;
          let shouldCast = false;
          let shouldCastTrue = true;
          if (isArray(propType)) {
            for (let index = 0; index < propType.length; ++index) {
              const type = propType[index];
              const typeName = isFunction(type) && type.name;
              if (typeName === "Boolean") {
                shouldCast = true;
                break;
              } else if (typeName === "String") {
                shouldCastTrue = false;
              }
            }
          } else {
            shouldCast = isFunction(propType) && propType.name === "Boolean";
          }
          prop[0] = shouldCast;
          prop[1] = shouldCastTrue;
          if (shouldCast || hasOwn(prop, "default")) {
            needCastKeys.push(normalizedKey);
          }
        }
      }
    }
    const res = [normalized, needCastKeys];
    if (isObject(comp)) {
      cache.set(comp, res);
    }
    return res;
  }
  function validatePropName(key) {
    if (key[0] !== "$" && !isReservedProp(key)) {
      return true;
    } else if (true) {
      warn$1(`Invalid prop name: "${key}" is a reserved property.`);
    }
    return false;
  }
  function getType(ctor) {
    if (ctor === null) {
      return "null";
    }
    if (typeof ctor === "function") {
      return ctor.name || "";
    } else if (typeof ctor === "object") {
      const name = ctor.constructor && ctor.constructor.name;
      return name || "";
    }
    return "";
  }
  function validateProps(rawProps, props, instance) {
    const resolvedValues = toRaw(props);
    const options = instance.propsOptions[0];
    const camelizePropsKey = Object.keys(rawProps).map((key) => camelize(key));
    for (const key in options) {
      let opt = options[key];
      if (opt == null)
        continue;
      validateProp(
        key,
        resolvedValues[key],
        opt,
        true ? shallowReadonly(resolvedValues) : resolvedValues,
        !camelizePropsKey.includes(key)
      );
    }
  }
  function validateProp(name, value, prop, props, isAbsent) {
    const { type, required, validator, skipCheck } = prop;
    if (required && isAbsent) {
      warn$1('Missing required prop: "' + name + '"');
      return;
    }
    if (value == null && !required) {
      return;
    }
    if (type != null && type !== true && !skipCheck) {
      let isValid = false;
      const types = isArray(type) ? type : [type];
      const expectedTypes = [];
      for (let i = 0; i < types.length && !isValid; i++) {
        const { valid, expectedType } = assertType(value, types[i]);
        expectedTypes.push(expectedType || "");
        isValid = valid;
      }
      if (!isValid) {
        warn$1(getInvalidTypeMessage(name, value, expectedTypes));
        return;
      }
    }
    if (validator && !validator(value, props)) {
      warn$1('Invalid prop: custom validator check failed for prop "' + name + '".');
    }
  }
  var isSimpleType = /* @__PURE__ */ makeMap(
    "String,Number,Boolean,Function,Symbol,BigInt"
  );
  function assertType(value, type) {
    let valid;
    const expectedType = getType(type);
    if (expectedType === "null") {
      valid = value === null;
    } else if (isSimpleType(expectedType)) {
      const t = typeof value;
      valid = t === expectedType.toLowerCase();
      if (!valid && t === "object") {
        valid = value instanceof type;
      }
    } else if (expectedType === "Object") {
      valid = isObject(value);
    } else if (expectedType === "Array") {
      valid = isArray(value);
    } else {
      valid = value instanceof type;
    }
    return {
      valid,
      expectedType
    };
  }
  function getInvalidTypeMessage(name, value, expectedTypes) {
    if (expectedTypes.length === 0) {
      return `Prop type [] for prop "${name}" won't match anything. Did you mean to use type Array instead?`;
    }
    let message = `Invalid prop: type check failed for prop "${name}". Expected ${expectedTypes.map(capitalize).join(" | ")}`;
    const expectedType = expectedTypes[0];
    const receivedType = toRawType(value);
    const expectedValue = styleValue(value, expectedType);
    const receivedValue = styleValue(value, receivedType);
    if (expectedTypes.length === 1 && isExplicable(expectedType) && !isBoolean(expectedType, receivedType)) {
      message += ` with value ${expectedValue}`;
    }
    message += `, got ${receivedType} `;
    if (isExplicable(receivedType)) {
      message += `with value ${receivedValue}.`;
    }
    return message;
  }
  function styleValue(value, type) {
    if (type === "String") {
      return `"${value}"`;
    } else if (type === "Number") {
      return `${Number(value)}`;
    } else {
      return `${value}`;
    }
  }
  function isExplicable(type) {
    const explicitTypes = ["string", "number", "boolean"];
    return explicitTypes.some((elem) => type.toLowerCase() === elem);
  }
  function isBoolean(...args) {
    return args.some((elem) => elem.toLowerCase() === "boolean");
  }
  var isInternalKey = (key) => key[0] === "_" || key === "$stable";
  var normalizeSlotValue = (value) => isArray(value) ? value.map(normalizeVNode) : [normalizeVNode(value)];
  var normalizeSlot = (key, rawSlot, ctx) => {
    if (rawSlot._n) {
      return rawSlot;
    }
    const normalized = withCtx((...args) => {
      if (currentInstance && (!ctx || ctx.root === currentInstance.root)) {
        warn$1(
          `Slot "${key}" invoked outside of the render function: this will not track dependencies used in the slot. Invoke the slot function inside the render function instead.`
        );
      }
      return normalizeSlotValue(rawSlot(...args));
    }, ctx);
    normalized._c = false;
    return normalized;
  };
  var normalizeObjectSlots = (rawSlots, slots, instance) => {
    const ctx = rawSlots._ctx;
    for (const key in rawSlots) {
      if (isInternalKey(key))
        continue;
      const value = rawSlots[key];
      if (isFunction(value)) {
        slots[key] = normalizeSlot(key, value, ctx);
      } else if (value != null) {
        if (true) {
          warn$1(
            `Non-function value encountered for slot "${key}". Prefer function slots for better performance.`
          );
        }
        const normalized = normalizeSlotValue(value);
        slots[key] = () => normalized;
      }
    }
  };
  var normalizeVNodeSlots = (instance, children) => {
    if (!isKeepAlive(instance.vnode) && true) {
      warn$1(
        `Non-function value encountered for default slot. Prefer function slots for better performance.`
      );
    }
    const normalized = normalizeSlotValue(children);
    instance.slots.default = () => normalized;
  };
  var assignSlots = (slots, children, optimized) => {
    for (const key in children) {
      if (optimized || key !== "_") {
        slots[key] = children[key];
      }
    }
  };
  var initSlots = (instance, children, optimized) => {
    const slots = instance.slots = createInternalObject();
    if (instance.vnode.shapeFlag & 32) {
      const type = children._;
      if (type) {
        assignSlots(slots, children, optimized);
        if (optimized) {
          def(slots, "_", type, true);
        }
      } else {
        normalizeObjectSlots(children, slots);
      }
    } else if (children) {
      normalizeVNodeSlots(instance, children);
    }
  };
  var updateSlots = (instance, children, optimized) => {
    const { vnode, slots } = instance;
    let needDeletionCheck = true;
    let deletionComparisonTarget = EMPTY_OBJ;
    if (vnode.shapeFlag & 32) {
      const type = children._;
      if (type) {
        if (isHmrUpdating) {
          assignSlots(slots, children, optimized);
          trigger(instance, "set", "$slots");
        } else if (optimized && type === 1) {
          needDeletionCheck = false;
        } else {
          assignSlots(slots, children, optimized);
        }
      } else {
        needDeletionCheck = !children.$stable;
        normalizeObjectSlots(children, slots);
      }
      deletionComparisonTarget = children;
    } else if (children) {
      normalizeVNodeSlots(instance, children);
      deletionComparisonTarget = { default: 1 };
    }
    if (needDeletionCheck) {
      for (const key in slots) {
        if (!isInternalKey(key) && deletionComparisonTarget[key] == null) {
          delete slots[key];
        }
      }
    }
  };
  var supported;
  var perf;
  function startMeasure(instance, type) {
    if (instance.appContext.config.performance && isSupported()) {
      perf.mark(`vue-${type}-${instance.uid}`);
    }
    if (true) {
      devtoolsPerfStart(instance, type, isSupported() ? perf.now() : Date.now());
    }
  }
  function endMeasure(instance, type) {
    if (instance.appContext.config.performance && isSupported()) {
      const startTag = `vue-${type}-${instance.uid}`;
      const endTag = startTag + `:end`;
      perf.mark(endTag);
      perf.measure(
        `<${formatComponentName(instance, instance.type)}> ${type}`,
        startTag,
        endTag
      );
      perf.clearMarks(startTag);
      perf.clearMarks(endTag);
    }
    if (true) {
      devtoolsPerfEnd(instance, type, isSupported() ? perf.now() : Date.now());
    }
  }
  function isSupported() {
    if (supported !== void 0) {
      return supported;
    }
    if (typeof window !== "undefined" && window.performance) {
      supported = true;
      perf = window.performance;
    } else {
      supported = false;
    }
    return supported;
  }
  function initFeatureFlags() {
    const needWarn = [];
    if (false) {
      needWarn.push(`__VUE_OPTIONS_API__`);
      getGlobalThis().__VUE_OPTIONS_API__ = true;
    }
    if (false) {
      needWarn.push(`__VUE_PROD_DEVTOOLS__`);
      getGlobalThis().__VUE_PROD_DEVTOOLS__ = false;
    }
    if (typeof __VUE_PROD_HYDRATION_MISMATCH_DETAILS__ !== "boolean") {
      needWarn.push(`__VUE_PROD_HYDRATION_MISMATCH_DETAILS__`);
      getGlobalThis().__VUE_PROD_HYDRATION_MISMATCH_DETAILS__ = false;
    }
    if (needWarn.length) {
      const multi = needWarn.length > 1;
      console.warn(
        `Feature flag${multi ? `s` : ``} ${needWarn.join(", ")} ${multi ? `are` : `is`} not explicitly defined. You are running the esm-bundler build of Vue, which expects these compile-time feature flags to be globally injected via the bundler config in order to get better tree-shaking in the production bundle.

For more details, see https://link.vuejs.org/feature-flags.`
      );
    }
  }
  var queuePostRenderEffect = queueEffectWithSuspense;
  function createRenderer(options) {
    return baseCreateRenderer(options);
  }
  function baseCreateRenderer(options, createHydrationFns) {
    {
      initFeatureFlags();
    }
    const target = getGlobalThis();
    target.__VUE__ = true;
    if (true) {
      setDevtoolsHook$1(target.__VUE_DEVTOOLS_GLOBAL_HOOK__, target);
    }
    const {
      insert: hostInsert,
      remove: hostRemove,
      patchProp: hostPatchProp,
      createElement: hostCreateElement,
      createText: hostCreateText,
      createComment: hostCreateComment,
      setText: hostSetText,
      setElementText: hostSetElementText,
      parentNode: hostParentNode,
      nextSibling: hostNextSibling,
      setScopeId: hostSetScopeId = NOOP,
      insertStaticContent: hostInsertStaticContent
    } = options;
    const patch = (n1, n2, container, anchor = null, parentComponent = null, parentSuspense = null, namespace = void 0, slotScopeIds = null, optimized = isHmrUpdating ? false : !!n2.dynamicChildren) => {
      if (n1 === n2) {
        return;
      }
      if (n1 && !isSameVNodeType(n1, n2)) {
        anchor = getNextHostNode(n1);
        unmount(n1, parentComponent, parentSuspense, true);
        n1 = null;
      }
      if (n2.patchFlag === -2) {
        optimized = false;
        n2.dynamicChildren = null;
      }
      const { type, ref: ref3, shapeFlag } = n2;
      switch (type) {
        case Text:
          processText(n1, n2, container, anchor);
          break;
        case Comment:
          processCommentNode(n1, n2, container, anchor);
          break;
        case Static:
          if (n1 == null) {
            mountStaticNode(n2, container, anchor, namespace);
          } else if (true) {
            patchStaticNode(n1, n2, container, namespace);
          }
          break;
        case Fragment:
          processFragment(
            n1,
            n2,
            container,
            anchor,
            parentComponent,
            parentSuspense,
            namespace,
            slotScopeIds,
            optimized
          );
          break;
        default:
          if (shapeFlag & 1) {
            processElement(
              n1,
              n2,
              container,
              anchor,
              parentComponent,
              parentSuspense,
              namespace,
              slotScopeIds,
              optimized
            );
          } else if (shapeFlag & 6) {
            processComponent(
              n1,
              n2,
              container,
              anchor,
              parentComponent,
              parentSuspense,
              namespace,
              slotScopeIds,
              optimized
            );
          } else if (shapeFlag & 64) {
            type.process(
              n1,
              n2,
              container,
              anchor,
              parentComponent,
              parentSuspense,
              namespace,
              slotScopeIds,
              optimized,
              internals
            );
          } else if (shapeFlag & 128) {
            type.process(
              n1,
              n2,
              container,
              anchor,
              parentComponent,
              parentSuspense,
              namespace,
              slotScopeIds,
              optimized,
              internals
            );
          } else if (true) {
            warn$1("Invalid VNode type:", type, `(${typeof type})`);
          }
      }
      if (ref3 != null && parentComponent) {
        setRef(ref3, n1 && n1.ref, parentSuspense, n2 || n1, !n2);
      }
    };
    const processText = (n1, n2, container, anchor) => {
      if (n1 == null) {
        hostInsert(
          n2.el = hostCreateText(n2.children),
          container,
          anchor
        );
      } else {
        const el = n2.el = n1.el;
        if (n2.children !== n1.children) {
          hostSetText(el, n2.children);
        }
      }
    };
    const processCommentNode = (n1, n2, container, anchor) => {
      if (n1 == null) {
        hostInsert(
          n2.el = hostCreateComment(n2.children || ""),
          container,
          anchor
        );
      } else {
        n2.el = n1.el;
      }
    };
    const mountStaticNode = (n2, container, anchor, namespace) => {
      [n2.el, n2.anchor] = hostInsertStaticContent(
        n2.children,
        container,
        anchor,
        namespace,
        n2.el,
        n2.anchor
      );
    };
    const patchStaticNode = (n1, n2, container, namespace) => {
      if (n2.children !== n1.children) {
        const anchor = hostNextSibling(n1.anchor);
        removeStaticNode(n1);
        [n2.el, n2.anchor] = hostInsertStaticContent(
          n2.children,
          container,
          anchor,
          namespace
        );
      } else {
        n2.el = n1.el;
        n2.anchor = n1.anchor;
      }
    };
    const moveStaticNode = ({ el, anchor }, container, nextSibling) => {
      let next;
      while (el && el !== anchor) {
        next = hostNextSibling(el);
        hostInsert(el, container, nextSibling);
        el = next;
      }
      hostInsert(anchor, container, nextSibling);
    };
    const removeStaticNode = ({ el, anchor }) => {
      let next;
      while (el && el !== anchor) {
        next = hostNextSibling(el);
        hostRemove(el);
        el = next;
      }
      hostRemove(anchor);
    };
    const processElement = (n1, n2, container, anchor, parentComponent, parentSuspense, namespace, slotScopeIds, optimized) => {
      if (n2.type === "svg") {
        namespace = "svg";
      } else if (n2.type === "math") {
        namespace = "mathml";
      }
      if (n1 == null) {
        mountElement(
          n2,
          container,
          anchor,
          parentComponent,
          parentSuspense,
          namespace,
          slotScopeIds,
          optimized
        );
      } else {
        patchElement(
          n1,
          n2,
          parentComponent,
          parentSuspense,
          namespace,
          slotScopeIds,
          optimized
        );
      }
    };
    const mountElement = (vnode, container, anchor, parentComponent, parentSuspense, namespace, slotScopeIds, optimized) => {
      let el;
      let vnodeHook;
      const { props, shapeFlag, transition, dirs } = vnode;
      el = vnode.el = hostCreateElement(
        vnode.type,
        namespace,
        props && props.is,
        props
      );
      if (shapeFlag & 8) {
        hostSetElementText(el, vnode.children);
      } else if (shapeFlag & 16) {
        mountChildren(
          vnode.children,
          el,
          null,
          parentComponent,
          parentSuspense,
          resolveChildrenNamespace(vnode, namespace),
          slotScopeIds,
          optimized
        );
      }
      if (dirs) {
        invokeDirectiveHook(vnode, null, parentComponent, "created");
      }
      setScopeId(el, vnode, vnode.scopeId, slotScopeIds, parentComponent);
      if (props) {
        for (const key in props) {
          if (key !== "value" && !isReservedProp(key)) {
            hostPatchProp(el, key, null, props[key], namespace, parentComponent);
          }
        }
        if ("value" in props) {
          hostPatchProp(el, "value", null, props.value, namespace);
        }
        if (vnodeHook = props.onVnodeBeforeMount) {
          invokeVNodeHook(vnodeHook, parentComponent, vnode);
        }
      }
      if (true) {
        def(el, "__vnode", vnode, true);
        def(el, "__vueParentComponent", parentComponent, true);
      }
      if (dirs) {
        invokeDirectiveHook(vnode, null, parentComponent, "beforeMount");
      }
      const needCallTransitionHooks = needTransition(parentSuspense, transition);
      if (needCallTransitionHooks) {
        transition.beforeEnter(el);
      }
      hostInsert(el, container, anchor);
      if ((vnodeHook = props && props.onVnodeMounted) || needCallTransitionHooks || dirs) {
        queuePostRenderEffect(() => {
          vnodeHook && invokeVNodeHook(vnodeHook, parentComponent, vnode);
          needCallTransitionHooks && transition.enter(el);
          dirs && invokeDirectiveHook(vnode, null, parentComponent, "mounted");
        }, parentSuspense);
      }
    };
    const setScopeId = (el, vnode, scopeId, slotScopeIds, parentComponent) => {
      if (scopeId) {
        hostSetScopeId(el, scopeId);
      }
      if (slotScopeIds) {
        for (let i = 0; i < slotScopeIds.length; i++) {
          hostSetScopeId(el, slotScopeIds[i]);
        }
      }
      if (parentComponent) {
        let subTree = parentComponent.subTree;
        if (subTree.patchFlag > 0 && subTree.patchFlag & 2048) {
          subTree = filterSingleRoot(subTree.children) || subTree;
        }
        if (vnode === subTree || isSuspense(subTree.type) && (subTree.ssContent === vnode || subTree.ssFallback === vnode)) {
          const parentVNode = parentComponent.vnode;
          setScopeId(
            el,
            parentVNode,
            parentVNode.scopeId,
            parentVNode.slotScopeIds,
            parentComponent.parent
          );
        }
      }
    };
    const mountChildren = (children, container, anchor, parentComponent, parentSuspense, namespace, slotScopeIds, optimized, start2 = 0) => {
      for (let i = start2; i < children.length; i++) {
        const child = children[i] = optimized ? cloneIfMounted(children[i]) : normalizeVNode(children[i]);
        patch(
          null,
          child,
          container,
          anchor,
          parentComponent,
          parentSuspense,
          namespace,
          slotScopeIds,
          optimized
        );
      }
    };
    const patchElement = (n1, n2, parentComponent, parentSuspense, namespace, slotScopeIds, optimized) => {
      const el = n2.el = n1.el;
      if (true) {
        el.__vnode = n2;
      }
      let { patchFlag, dynamicChildren, dirs } = n2;
      patchFlag |= n1.patchFlag & 16;
      const oldProps = n1.props || EMPTY_OBJ;
      const newProps = n2.props || EMPTY_OBJ;
      let vnodeHook;
      parentComponent && toggleRecurse(parentComponent, false);
      if (vnodeHook = newProps.onVnodeBeforeUpdate) {
        invokeVNodeHook(vnodeHook, parentComponent, n2, n1);
      }
      if (dirs) {
        invokeDirectiveHook(n2, n1, parentComponent, "beforeUpdate");
      }
      parentComponent && toggleRecurse(parentComponent, true);
      if (isHmrUpdating) {
        patchFlag = 0;
        optimized = false;
        dynamicChildren = null;
      }
      if (oldProps.innerHTML && newProps.innerHTML == null || oldProps.textContent && newProps.textContent == null) {
        hostSetElementText(el, "");
      }
      if (dynamicChildren) {
        patchBlockChildren(
          n1.dynamicChildren,
          dynamicChildren,
          el,
          parentComponent,
          parentSuspense,
          resolveChildrenNamespace(n2, namespace),
          slotScopeIds
        );
        if (true) {
          traverseStaticChildren(n1, n2);
        }
      } else if (!optimized) {
        patchChildren(
          n1,
          n2,
          el,
          null,
          parentComponent,
          parentSuspense,
          resolveChildrenNamespace(n2, namespace),
          slotScopeIds,
          false
        );
      }
      if (patchFlag > 0) {
        if (patchFlag & 16) {
          patchProps(el, oldProps, newProps, parentComponent, namespace);
        } else {
          if (patchFlag & 2) {
            if (oldProps.class !== newProps.class) {
              hostPatchProp(el, "class", null, newProps.class, namespace);
            }
          }
          if (patchFlag & 4) {
            hostPatchProp(el, "style", oldProps.style, newProps.style, namespace);
          }
          if (patchFlag & 8) {
            const propsToUpdate = n2.dynamicProps;
            for (let i = 0; i < propsToUpdate.length; i++) {
              const key = propsToUpdate[i];
              const prev = oldProps[key];
              const next = newProps[key];
              if (next !== prev || key === "value") {
                hostPatchProp(el, key, prev, next, namespace, parentComponent);
              }
            }
          }
        }
        if (patchFlag & 1) {
          if (n1.children !== n2.children) {
            hostSetElementText(el, n2.children);
          }
        }
      } else if (!optimized && dynamicChildren == null) {
        patchProps(el, oldProps, newProps, parentComponent, namespace);
      }
      if ((vnodeHook = newProps.onVnodeUpdated) || dirs) {
        queuePostRenderEffect(() => {
          vnodeHook && invokeVNodeHook(vnodeHook, parentComponent, n2, n1);
          dirs && invokeDirectiveHook(n2, n1, parentComponent, "updated");
        }, parentSuspense);
      }
    };
    const patchBlockChildren = (oldChildren, newChildren, fallbackContainer, parentComponent, parentSuspense, namespace, slotScopeIds) => {
      for (let i = 0; i < newChildren.length; i++) {
        const oldVNode = oldChildren[i];
        const newVNode = newChildren[i];
        const container = oldVNode.el && (oldVNode.type === Fragment || !isSameVNodeType(oldVNode, newVNode) || oldVNode.shapeFlag & (6 | 64)) ? hostParentNode(oldVNode.el) : fallbackContainer;
        patch(
          oldVNode,
          newVNode,
          container,
          null,
          parentComponent,
          parentSuspense,
          namespace,
          slotScopeIds,
          true
        );
      }
    };
    const patchProps = (el, oldProps, newProps, parentComponent, namespace) => {
      if (oldProps !== newProps) {
        if (oldProps !== EMPTY_OBJ) {
          for (const key in oldProps) {
            if (!isReservedProp(key) && !(key in newProps)) {
              hostPatchProp(
                el,
                key,
                oldProps[key],
                null,
                namespace,
                parentComponent
              );
            }
          }
        }
        for (const key in newProps) {
          if (isReservedProp(key))
            continue;
          const next = newProps[key];
          const prev = oldProps[key];
          if (next !== prev && key !== "value") {
            hostPatchProp(el, key, prev, next, namespace, parentComponent);
          }
        }
        if ("value" in newProps) {
          hostPatchProp(el, "value", oldProps.value, newProps.value, namespace);
        }
      }
    };
    const processFragment = (n1, n2, container, anchor, parentComponent, parentSuspense, namespace, slotScopeIds, optimized) => {
      const fragmentStartAnchor = n2.el = n1 ? n1.el : hostCreateText("");
      const fragmentEndAnchor = n2.anchor = n1 ? n1.anchor : hostCreateText("");
      let { patchFlag, dynamicChildren, slotScopeIds: fragmentSlotScopeIds } = n2;
      if (isHmrUpdating || patchFlag & 2048) {
        patchFlag = 0;
        optimized = false;
        dynamicChildren = null;
      }
      if (fragmentSlotScopeIds) {
        slotScopeIds = slotScopeIds ? slotScopeIds.concat(fragmentSlotScopeIds) : fragmentSlotScopeIds;
      }
      if (n1 == null) {
        hostInsert(fragmentStartAnchor, container, anchor);
        hostInsert(fragmentEndAnchor, container, anchor);
        mountChildren(
          n2.children || [],
          container,
          fragmentEndAnchor,
          parentComponent,
          parentSuspense,
          namespace,
          slotScopeIds,
          optimized
        );
      } else {
        if (patchFlag > 0 && patchFlag & 64 && dynamicChildren && n1.dynamicChildren) {
          patchBlockChildren(
            n1.dynamicChildren,
            dynamicChildren,
            container,
            parentComponent,
            parentSuspense,
            namespace,
            slotScopeIds
          );
          if (true) {
            traverseStaticChildren(n1, n2);
          } else if (n2.key != null || parentComponent && n2 === parentComponent.subTree) {
            traverseStaticChildren(
              n1,
              n2,
              true
            );
          }
        } else {
          patchChildren(
            n1,
            n2,
            container,
            fragmentEndAnchor,
            parentComponent,
            parentSuspense,
            namespace,
            slotScopeIds,
            optimized
          );
        }
      }
    };
    const processComponent = (n1, n2, container, anchor, parentComponent, parentSuspense, namespace, slotScopeIds, optimized) => {
      n2.slotScopeIds = slotScopeIds;
      if (n1 == null) {
        if (n2.shapeFlag & 512) {
          parentComponent.ctx.activate(
            n2,
            container,
            anchor,
            namespace,
            optimized
          );
        } else {
          mountComponent(
            n2,
            container,
            anchor,
            parentComponent,
            parentSuspense,
            namespace,
            optimized
          );
        }
      } else {
        updateComponent(n1, n2, optimized);
      }
    };
    const mountComponent = (initialVNode, container, anchor, parentComponent, parentSuspense, namespace, optimized) => {
      const instance = initialVNode.component = createComponentInstance(
        initialVNode,
        parentComponent,
        parentSuspense
      );
      if (instance.type.__hmrId) {
        registerHMR(instance);
      }
      if (true) {
        pushWarningContext(initialVNode);
        startMeasure(instance, `mount`);
      }
      if (isKeepAlive(initialVNode)) {
        instance.ctx.renderer = internals;
      }
      {
        if (true) {
          startMeasure(instance, `init`);
        }
        setupComponent(instance, false, optimized);
        if (true) {
          endMeasure(instance, `init`);
        }
      }
      if (instance.asyncDep) {
        if (isHmrUpdating)
          initialVNode.el = null;
        parentSuspense && parentSuspense.registerDep(instance, setupRenderEffect, optimized);
        if (!initialVNode.el) {
          const placeholder = instance.subTree = createVNode(Comment);
          processCommentNode(null, placeholder, container, anchor);
        }
      } else {
        setupRenderEffect(
          instance,
          initialVNode,
          container,
          anchor,
          parentSuspense,
          namespace,
          optimized
        );
      }
      if (true) {
        popWarningContext();
        endMeasure(instance, `mount`);
      }
    };
    const updateComponent = (n1, n2, optimized) => {
      const instance = n2.component = n1.component;
      if (shouldUpdateComponent(n1, n2, optimized)) {
        if (instance.asyncDep && !instance.asyncResolved) {
          if (true) {
            pushWarningContext(n2);
          }
          updateComponentPreRender(instance, n2, optimized);
          if (true) {
            popWarningContext();
          }
          return;
        } else {
          instance.next = n2;
          instance.update();
        }
      } else {
        n2.el = n1.el;
        instance.vnode = n2;
      }
    };
    const setupRenderEffect = (instance, initialVNode, container, anchor, parentSuspense, namespace, optimized) => {
      const componentUpdateFn = () => {
        if (!instance.isMounted) {
          let vnodeHook;
          const { el, props } = initialVNode;
          const { bm, m, parent, root, type } = instance;
          const isAsyncWrapperVNode = isAsyncWrapper(initialVNode);
          toggleRecurse(instance, false);
          if (bm) {
            invokeArrayFns(bm);
          }
          if (!isAsyncWrapperVNode && (vnodeHook = props && props.onVnodeBeforeMount)) {
            invokeVNodeHook(vnodeHook, parent, initialVNode);
          }
          toggleRecurse(instance, true);
          if (el && hydrateNode) {
            const hydrateSubTree = () => {
              if (true) {
                startMeasure(instance, `render`);
              }
              instance.subTree = renderComponentRoot(instance);
              if (true) {
                endMeasure(instance, `render`);
              }
              if (true) {
                startMeasure(instance, `hydrate`);
              }
              hydrateNode(
                el,
                instance.subTree,
                instance,
                parentSuspense,
                null
              );
              if (true) {
                endMeasure(instance, `hydrate`);
              }
            };
            if (isAsyncWrapperVNode && type.__asyncHydrate) {
              type.__asyncHydrate(
                el,
                instance,
                hydrateSubTree
              );
            } else {
              hydrateSubTree();
            }
          } else {
            if (root.ce) {
              root.ce._injectChildStyle(type);
            }
            if (true) {
              startMeasure(instance, `render`);
            }
            const subTree = instance.subTree = renderComponentRoot(instance);
            if (true) {
              endMeasure(instance, `render`);
            }
            if (true) {
              startMeasure(instance, `patch`);
            }
            patch(
              null,
              subTree,
              container,
              anchor,
              instance,
              parentSuspense,
              namespace
            );
            if (true) {
              endMeasure(instance, `patch`);
            }
            initialVNode.el = subTree.el;
          }
          if (m) {
            queuePostRenderEffect(m, parentSuspense);
          }
          if (!isAsyncWrapperVNode && (vnodeHook = props && props.onVnodeMounted)) {
            const scopedInitialVNode = initialVNode;
            queuePostRenderEffect(
              () => invokeVNodeHook(vnodeHook, parent, scopedInitialVNode),
              parentSuspense
            );
          }
          if (initialVNode.shapeFlag & 256 || parent && isAsyncWrapper(parent.vnode) && parent.vnode.shapeFlag & 256) {
            instance.a && queuePostRenderEffect(instance.a, parentSuspense);
          }
          instance.isMounted = true;
          if (true) {
            devtoolsComponentAdded(instance);
          }
          initialVNode = container = anchor = null;
        } else {
          let { next, bu, u, parent, vnode } = instance;
          {
            const nonHydratedAsyncRoot = locateNonHydratedAsyncRoot(instance);
            if (nonHydratedAsyncRoot) {
              if (next) {
                next.el = vnode.el;
                updateComponentPreRender(instance, next, optimized);
              }
              nonHydratedAsyncRoot.asyncDep.then(() => {
                if (!instance.isUnmounted) {
                  componentUpdateFn();
                }
              });
              return;
            }
          }
          let originNext = next;
          let vnodeHook;
          if (true) {
            pushWarningContext(next || instance.vnode);
          }
          toggleRecurse(instance, false);
          if (next) {
            next.el = vnode.el;
            updateComponentPreRender(instance, next, optimized);
          } else {
            next = vnode;
          }
          if (bu) {
            invokeArrayFns(bu);
          }
          if (vnodeHook = next.props && next.props.onVnodeBeforeUpdate) {
            invokeVNodeHook(vnodeHook, parent, next, vnode);
          }
          toggleRecurse(instance, true);
          if (true) {
            startMeasure(instance, `render`);
          }
          const nextTree = renderComponentRoot(instance);
          if (true) {
            endMeasure(instance, `render`);
          }
          const prevTree = instance.subTree;
          instance.subTree = nextTree;
          if (true) {
            startMeasure(instance, `patch`);
          }
          patch(
            prevTree,
            nextTree,
            hostParentNode(prevTree.el),
            getNextHostNode(prevTree),
            instance,
            parentSuspense,
            namespace
          );
          if (true) {
            endMeasure(instance, `patch`);
          }
          next.el = nextTree.el;
          if (originNext === null) {
            updateHOCHostEl(instance, nextTree.el);
          }
          if (u) {
            queuePostRenderEffect(u, parentSuspense);
          }
          if (vnodeHook = next.props && next.props.onVnodeUpdated) {
            queuePostRenderEffect(
              () => invokeVNodeHook(vnodeHook, parent, next, vnode),
              parentSuspense
            );
          }
          if (true) {
            devtoolsComponentUpdated(instance);
          }
          if (true) {
            popWarningContext();
          }
        }
      };
      instance.scope.on();
      const effect6 = instance.effect = new ReactiveEffect(componentUpdateFn);
      instance.scope.off();
      const update = instance.update = effect6.run.bind(effect6);
      const job = instance.job = effect6.runIfDirty.bind(effect6);
      job.i = instance;
      job.id = instance.uid;
      effect6.scheduler = () => queueJob(job);
      toggleRecurse(instance, true);
      if (true) {
        effect6.onTrack = instance.rtc ? (e) => invokeArrayFns(instance.rtc, e) : void 0;
        effect6.onTrigger = instance.rtg ? (e) => invokeArrayFns(instance.rtg, e) : void 0;
      }
      update();
    };
    const updateComponentPreRender = (instance, nextVNode, optimized) => {
      nextVNode.component = instance;
      const prevProps = instance.vnode.props;
      instance.vnode = nextVNode;
      instance.next = null;
      updateProps(instance, nextVNode.props, prevProps, optimized);
      updateSlots(instance, nextVNode.children, optimized);
      pauseTracking();
      flushPreFlushCbs(instance);
      resetTracking();
    };
    const patchChildren = (n1, n2, container, anchor, parentComponent, parentSuspense, namespace, slotScopeIds, optimized = false) => {
      const c1 = n1 && n1.children;
      const prevShapeFlag = n1 ? n1.shapeFlag : 0;
      const c2 = n2.children;
      const { patchFlag, shapeFlag } = n2;
      if (patchFlag > 0) {
        if (patchFlag & 128) {
          patchKeyedChildren(
            c1,
            c2,
            container,
            anchor,
            parentComponent,
            parentSuspense,
            namespace,
            slotScopeIds,
            optimized
          );
          return;
        } else if (patchFlag & 256) {
          patchUnkeyedChildren(
            c1,
            c2,
            container,
            anchor,
            parentComponent,
            parentSuspense,
            namespace,
            slotScopeIds,
            optimized
          );
          return;
        }
      }
      if (shapeFlag & 8) {
        if (prevShapeFlag & 16) {
          unmountChildren(c1, parentComponent, parentSuspense);
        }
        if (c2 !== c1) {
          hostSetElementText(container, c2);
        }
      } else {
        if (prevShapeFlag & 16) {
          if (shapeFlag & 16) {
            patchKeyedChildren(
              c1,
              c2,
              container,
              anchor,
              parentComponent,
              parentSuspense,
              namespace,
              slotScopeIds,
              optimized
            );
          } else {
            unmountChildren(c1, parentComponent, parentSuspense, true);
          }
        } else {
          if (prevShapeFlag & 8) {
            hostSetElementText(container, "");
          }
          if (shapeFlag & 16) {
            mountChildren(
              c2,
              container,
              anchor,
              parentComponent,
              parentSuspense,
              namespace,
              slotScopeIds,
              optimized
            );
          }
        }
      }
    };
    const patchUnkeyedChildren = (c1, c2, container, anchor, parentComponent, parentSuspense, namespace, slotScopeIds, optimized) => {
      c1 = c1 || EMPTY_ARR;
      c2 = c2 || EMPTY_ARR;
      const oldLength = c1.length;
      const newLength = c2.length;
      const commonLength = Math.min(oldLength, newLength);
      let i;
      for (i = 0; i < commonLength; i++) {
        const nextChild = c2[i] = optimized ? cloneIfMounted(c2[i]) : normalizeVNode(c2[i]);
        patch(
          c1[i],
          nextChild,
          container,
          null,
          parentComponent,
          parentSuspense,
          namespace,
          slotScopeIds,
          optimized
        );
      }
      if (oldLength > newLength) {
        unmountChildren(
          c1,
          parentComponent,
          parentSuspense,
          true,
          false,
          commonLength
        );
      } else {
        mountChildren(
          c2,
          container,
          anchor,
          parentComponent,
          parentSuspense,
          namespace,
          slotScopeIds,
          optimized,
          commonLength
        );
      }
    };
    const patchKeyedChildren = (c1, c2, container, parentAnchor, parentComponent, parentSuspense, namespace, slotScopeIds, optimized) => {
      let i = 0;
      const l2 = c2.length;
      let e1 = c1.length - 1;
      let e2 = l2 - 1;
      while (i <= e1 && i <= e2) {
        const n1 = c1[i];
        const n2 = c2[i] = optimized ? cloneIfMounted(c2[i]) : normalizeVNode(c2[i]);
        if (isSameVNodeType(n1, n2)) {
          patch(
            n1,
            n2,
            container,
            null,
            parentComponent,
            parentSuspense,
            namespace,
            slotScopeIds,
            optimized
          );
        } else {
          break;
        }
        i++;
      }
      while (i <= e1 && i <= e2) {
        const n1 = c1[e1];
        const n2 = c2[e2] = optimized ? cloneIfMounted(c2[e2]) : normalizeVNode(c2[e2]);
        if (isSameVNodeType(n1, n2)) {
          patch(
            n1,
            n2,
            container,
            null,
            parentComponent,
            parentSuspense,
            namespace,
            slotScopeIds,
            optimized
          );
        } else {
          break;
        }
        e1--;
        e2--;
      }
      if (i > e1) {
        if (i <= e2) {
          const nextPos = e2 + 1;
          const anchor = nextPos < l2 ? c2[nextPos].el : parentAnchor;
          while (i <= e2) {
            patch(
              null,
              c2[i] = optimized ? cloneIfMounted(c2[i]) : normalizeVNode(c2[i]),
              container,
              anchor,
              parentComponent,
              parentSuspense,
              namespace,
              slotScopeIds,
              optimized
            );
            i++;
          }
        }
      } else if (i > e2) {
        while (i <= e1) {
          unmount(c1[i], parentComponent, parentSuspense, true);
          i++;
        }
      } else {
        const s1 = i;
        const s2 = i;
        const keyToNewIndexMap = /* @__PURE__ */ new Map();
        for (i = s2; i <= e2; i++) {
          const nextChild = c2[i] = optimized ? cloneIfMounted(c2[i]) : normalizeVNode(c2[i]);
          if (nextChild.key != null) {
            if (keyToNewIndexMap.has(nextChild.key)) {
              warn$1(
                `Duplicate keys found during update:`,
                JSON.stringify(nextChild.key),
                `Make sure keys are unique.`
              );
            }
            keyToNewIndexMap.set(nextChild.key, i);
          }
        }
        let j;
        let patched = 0;
        const toBePatched = e2 - s2 + 1;
        let moved = false;
        let maxNewIndexSoFar = 0;
        const newIndexToOldIndexMap = new Array(toBePatched);
        for (i = 0; i < toBePatched; i++)
          newIndexToOldIndexMap[i] = 0;
        for (i = s1; i <= e1; i++) {
          const prevChild = c1[i];
          if (patched >= toBePatched) {
            unmount(prevChild, parentComponent, parentSuspense, true);
            continue;
          }
          let newIndex;
          if (prevChild.key != null) {
            newIndex = keyToNewIndexMap.get(prevChild.key);
          } else {
            for (j = s2; j <= e2; j++) {
              if (newIndexToOldIndexMap[j - s2] === 0 && isSameVNodeType(prevChild, c2[j])) {
                newIndex = j;
                break;
              }
            }
          }
          if (newIndex === void 0) {
            unmount(prevChild, parentComponent, parentSuspense, true);
          } else {
            newIndexToOldIndexMap[newIndex - s2] = i + 1;
            if (newIndex >= maxNewIndexSoFar) {
              maxNewIndexSoFar = newIndex;
            } else {
              moved = true;
            }
            patch(
              prevChild,
              c2[newIndex],
              container,
              null,
              parentComponent,
              parentSuspense,
              namespace,
              slotScopeIds,
              optimized
            );
            patched++;
          }
        }
        const increasingNewIndexSequence = moved ? getSequence(newIndexToOldIndexMap) : EMPTY_ARR;
        j = increasingNewIndexSequence.length - 1;
        for (i = toBePatched - 1; i >= 0; i--) {
          const nextIndex = s2 + i;
          const nextChild = c2[nextIndex];
          const anchor = nextIndex + 1 < l2 ? c2[nextIndex + 1].el : parentAnchor;
          if (newIndexToOldIndexMap[i] === 0) {
            patch(
              null,
              nextChild,
              container,
              anchor,
              parentComponent,
              parentSuspense,
              namespace,
              slotScopeIds,
              optimized
            );
          } else if (moved) {
            if (j < 0 || i !== increasingNewIndexSequence[j]) {
              move(nextChild, container, anchor, 2);
            } else {
              j--;
            }
          }
        }
      }
    };
    const move = (vnode, container, anchor, moveType, parentSuspense = null) => {
      const { el, type, transition, children, shapeFlag } = vnode;
      if (shapeFlag & 6) {
        move(vnode.component.subTree, container, anchor, moveType);
        return;
      }
      if (shapeFlag & 128) {
        vnode.suspense.move(container, anchor, moveType);
        return;
      }
      if (shapeFlag & 64) {
        type.move(vnode, container, anchor, internals);
        return;
      }
      if (type === Fragment) {
        hostInsert(el, container, anchor);
        for (let i = 0; i < children.length; i++) {
          move(children[i], container, anchor, moveType);
        }
        hostInsert(vnode.anchor, container, anchor);
        return;
      }
      if (type === Static) {
        moveStaticNode(vnode, container, anchor);
        return;
      }
      const needTransition2 = moveType !== 2 && shapeFlag & 1 && transition;
      if (needTransition2) {
        if (moveType === 0) {
          transition.beforeEnter(el);
          hostInsert(el, container, anchor);
          queuePostRenderEffect(() => transition.enter(el), parentSuspense);
        } else {
          const { leave, delayLeave, afterLeave } = transition;
          const remove22 = () => hostInsert(el, container, anchor);
          const performLeave = () => {
            leave(el, () => {
              remove22();
              afterLeave && afterLeave();
            });
          };
          if (delayLeave) {
            delayLeave(el, remove22, performLeave);
          } else {
            performLeave();
          }
        }
      } else {
        hostInsert(el, container, anchor);
      }
    };
    const unmount = (vnode, parentComponent, parentSuspense, doRemove = false, optimized = false) => {
      const {
        type,
        props,
        ref: ref3,
        children,
        dynamicChildren,
        shapeFlag,
        patchFlag,
        dirs,
        cacheIndex
      } = vnode;
      if (patchFlag === -2) {
        optimized = false;
      }
      if (ref3 != null) {
        setRef(ref3, null, parentSuspense, vnode, true);
      }
      if (cacheIndex != null) {
        parentComponent.renderCache[cacheIndex] = void 0;
      }
      if (shapeFlag & 256) {
        parentComponent.ctx.deactivate(vnode);
        return;
      }
      const shouldInvokeDirs = shapeFlag & 1 && dirs;
      const shouldInvokeVnodeHook = !isAsyncWrapper(vnode);
      let vnodeHook;
      if (shouldInvokeVnodeHook && (vnodeHook = props && props.onVnodeBeforeUnmount)) {
        invokeVNodeHook(vnodeHook, parentComponent, vnode);
      }
      if (shapeFlag & 6) {
        unmountComponent(vnode.component, parentSuspense, doRemove);
      } else {
        if (shapeFlag & 128) {
          vnode.suspense.unmount(parentSuspense, doRemove);
          return;
        }
        if (shouldInvokeDirs) {
          invokeDirectiveHook(vnode, null, parentComponent, "beforeUnmount");
        }
        if (shapeFlag & 64) {
          vnode.type.remove(
            vnode,
            parentComponent,
            parentSuspense,
            internals,
            doRemove
          );
        } else if (dynamicChildren && !dynamicChildren.hasOnce && (type !== Fragment || patchFlag > 0 && patchFlag & 64)) {
          unmountChildren(
            dynamicChildren,
            parentComponent,
            parentSuspense,
            false,
            true
          );
        } else if (type === Fragment && patchFlag & (128 | 256) || !optimized && shapeFlag & 16) {
          unmountChildren(children, parentComponent, parentSuspense);
        }
        if (doRemove) {
          remove3(vnode);
        }
      }
      if (shouldInvokeVnodeHook && (vnodeHook = props && props.onVnodeUnmounted) || shouldInvokeDirs) {
        queuePostRenderEffect(() => {
          vnodeHook && invokeVNodeHook(vnodeHook, parentComponent, vnode);
          shouldInvokeDirs && invokeDirectiveHook(vnode, null, parentComponent, "unmounted");
        }, parentSuspense);
      }
    };
    const remove3 = (vnode) => {
      const { type, el, anchor, transition } = vnode;
      if (type === Fragment) {
        if (vnode.patchFlag > 0 && vnode.patchFlag & 2048 && transition && !transition.persisted) {
          vnode.children.forEach((child) => {
            if (child.type === Comment) {
              hostRemove(child.el);
            } else {
              remove3(child);
            }
          });
        } else {
          removeFragment(el, anchor);
        }
        return;
      }
      if (type === Static) {
        removeStaticNode(vnode);
        return;
      }
      const performRemove = () => {
        hostRemove(el);
        if (transition && !transition.persisted && transition.afterLeave) {
          transition.afterLeave();
        }
      };
      if (vnode.shapeFlag & 1 && transition && !transition.persisted) {
        const { leave, delayLeave } = transition;
        const performLeave = () => leave(el, performRemove);
        if (delayLeave) {
          delayLeave(vnode.el, performRemove, performLeave);
        } else {
          performLeave();
        }
      } else {
        performRemove();
      }
    };
    const removeFragment = (cur, end2) => {
      let next;
      while (cur !== end2) {
        next = hostNextSibling(cur);
        hostRemove(cur);
        cur = next;
      }
      hostRemove(end2);
    };
    const unmountComponent = (instance, parentSuspense, doRemove) => {
      if (instance.type.__hmrId) {
        unregisterHMR(instance);
      }
      const { bum, scope, job, subTree, um, m, a } = instance;
      invalidateMount(m);
      invalidateMount(a);
      if (bum) {
        invokeArrayFns(bum);
      }
      scope.stop();
      if (job) {
        job.flags |= 8;
        unmount(subTree, instance, parentSuspense, doRemove);
      }
      if (um) {
        queuePostRenderEffect(um, parentSuspense);
      }
      queuePostRenderEffect(() => {
        instance.isUnmounted = true;
      }, parentSuspense);
      if (parentSuspense && parentSuspense.pendingBranch && !parentSuspense.isUnmounted && instance.asyncDep && !instance.asyncResolved && instance.suspenseId === parentSuspense.pendingId) {
        parentSuspense.deps--;
        if (parentSuspense.deps === 0) {
          parentSuspense.resolve();
        }
      }
      if (true) {
        devtoolsComponentRemoved(instance);
      }
    };
    const unmountChildren = (children, parentComponent, parentSuspense, doRemove = false, optimized = false, start2 = 0) => {
      for (let i = start2; i < children.length; i++) {
        unmount(children[i], parentComponent, parentSuspense, doRemove, optimized);
      }
    };
    const getNextHostNode = (vnode) => {
      if (vnode.shapeFlag & 6) {
        return getNextHostNode(vnode.component.subTree);
      }
      if (vnode.shapeFlag & 128) {
        return vnode.suspense.next();
      }
      const el = hostNextSibling(vnode.anchor || vnode.el);
      const teleportEnd = el && el[TeleportEndKey];
      return teleportEnd ? hostNextSibling(teleportEnd) : el;
    };
    let isFlushing2 = false;
    const render8 = (vnode, container, namespace) => {
      if (vnode == null) {
        if (container._vnode) {
          unmount(container._vnode, null, null, true);
        }
      } else {
        patch(
          container._vnode || null,
          vnode,
          container,
          null,
          null,
          null,
          namespace
        );
      }
      container._vnode = vnode;
      if (!isFlushing2) {
        isFlushing2 = true;
        flushPreFlushCbs();
        flushPostFlushCbs();
        isFlushing2 = false;
      }
    };
    const internals = {
      p: patch,
      um: unmount,
      m: move,
      r: remove3,
      mt: mountComponent,
      mc: mountChildren,
      pc: patchChildren,
      pbc: patchBlockChildren,
      n: getNextHostNode,
      o: options
    };
    let hydrate;
    let hydrateNode;
    if (createHydrationFns) {
      [hydrate, hydrateNode] = createHydrationFns(
        internals
      );
    }
    return {
      render: render8,
      hydrate,
      createApp: createAppAPI(render8, hydrate)
    };
  }
  function resolveChildrenNamespace({ type, props }, currentNamespace) {
    return currentNamespace === "svg" && type === "foreignObject" || currentNamespace === "mathml" && type === "annotation-xml" && props && props.encoding && props.encoding.includes("html") ? void 0 : currentNamespace;
  }
  function toggleRecurse({ effect: effect6, job }, allowed) {
    if (allowed) {
      effect6.flags |= 32;
      job.flags |= 4;
    } else {
      effect6.flags &= ~32;
      job.flags &= ~4;
    }
  }
  function needTransition(parentSuspense, transition) {
    return (!parentSuspense || parentSuspense && !parentSuspense.pendingBranch) && transition && !transition.persisted;
  }
  function traverseStaticChildren(n1, n2, shallow = false) {
    const ch1 = n1.children;
    const ch2 = n2.children;
    if (isArray(ch1) && isArray(ch2)) {
      for (let i = 0; i < ch1.length; i++) {
        const c1 = ch1[i];
        let c2 = ch2[i];
        if (c2.shapeFlag & 1 && !c2.dynamicChildren) {
          if (c2.patchFlag <= 0 || c2.patchFlag === 32) {
            c2 = ch2[i] = cloneIfMounted(ch2[i]);
            c2.el = c1.el;
          }
          if (!shallow && c2.patchFlag !== -2)
            traverseStaticChildren(c1, c2);
        }
        if (c2.type === Text) {
          c2.el = c1.el;
        }
        if (c2.type === Comment && !c2.el) {
          c2.el = c1.el;
        }
      }
    }
  }
  function getSequence(arr) {
    const p2 = arr.slice();
    const result = [0];
    let i, j, u, v, c;
    const len = arr.length;
    for (i = 0; i < len; i++) {
      const arrI = arr[i];
      if (arrI !== 0) {
        j = result[result.length - 1];
        if (arr[j] < arrI) {
          p2[i] = j;
          result.push(i);
          continue;
        }
        u = 0;
        v = result.length - 1;
        while (u < v) {
          c = u + v >> 1;
          if (arr[result[c]] < arrI) {
            u = c + 1;
          } else {
            v = c;
          }
        }
        if (arrI < arr[result[u]]) {
          if (u > 0) {
            p2[i] = result[u - 1];
          }
          result[u] = i;
        }
      }
    }
    u = result.length;
    v = result[u - 1];
    while (u-- > 0) {
      result[u] = v;
      v = p2[v];
    }
    return result;
  }
  function locateNonHydratedAsyncRoot(instance) {
    const subComponent = instance.subTree.component;
    if (subComponent) {
      if (subComponent.asyncDep && !subComponent.asyncResolved) {
        return subComponent;
      } else {
        return locateNonHydratedAsyncRoot(subComponent);
      }
    }
  }
  function invalidateMount(hooks) {
    if (hooks) {
      for (let i = 0; i < hooks.length; i++)
        hooks[i].flags |= 8;
    }
  }
  var ssrContextKey = Symbol.for("v-scx");
  var useSSRContext = () => {
    {
      const ctx = inject(ssrContextKey);
      if (!ctx) {
        warn$1(
          `Server rendering context not provided. Make sure to only call useSSRContext() conditionally in the server build.`
        );
      }
      return ctx;
    }
  };
  function watch2(source, cb, options) {
    if (!isFunction(cb)) {
      warn$1(
        `\`watch(fn, options?)\` signature has been moved to a separate API. Use \`watchEffect(fn, options?)\` instead. \`watch\` now only supports \`watch(source, cb, options?) signature.`
      );
    }
    return doWatch(source, cb, options);
  }
  function doWatch(source, cb, options = EMPTY_OBJ) {
    const { immediate, deep, flush, once } = options;
    if (!cb) {
      if (immediate !== void 0) {
        warn$1(
          `watch() "immediate" option is only respected when using the watch(source, callback, options?) signature.`
        );
      }
      if (deep !== void 0) {
        warn$1(
          `watch() "deep" option is only respected when using the watch(source, callback, options?) signature.`
        );
      }
      if (once !== void 0) {
        warn$1(
          `watch() "once" option is only respected when using the watch(source, callback, options?) signature.`
        );
      }
    }
    const baseWatchOptions = extend({}, options);
    if (true)
      baseWatchOptions.onWarn = warn$1;
    const runsImmediately = cb && immediate || !cb && flush !== "post";
    let ssrCleanup;
    if (isInSSRComponentSetup) {
      if (flush === "sync") {
        const ctx = useSSRContext();
        ssrCleanup = ctx.__watcherHandles || (ctx.__watcherHandles = []);
      } else if (!runsImmediately) {
        const watchStopHandle = () => {
        };
        watchStopHandle.stop = NOOP;
        watchStopHandle.resume = NOOP;
        watchStopHandle.pause = NOOP;
        return watchStopHandle;
      }
    }
    const instance = currentInstance;
    baseWatchOptions.call = (fn2, type, args) => callWithAsyncErrorHandling(fn2, instance, type, args);
    let isPre = false;
    if (flush === "post") {
      baseWatchOptions.scheduler = (job) => {
        queuePostRenderEffect(job, instance && instance.suspense);
      };
    } else if (flush !== "sync") {
      isPre = true;
      baseWatchOptions.scheduler = (job, isFirstRun) => {
        if (isFirstRun) {
          job();
        } else {
          queueJob(job);
        }
      };
    }
    baseWatchOptions.augmentJob = (job) => {
      if (cb) {
        job.flags |= 4;
      }
      if (isPre) {
        job.flags |= 2;
        if (instance) {
          job.id = instance.uid;
          job.i = instance;
        }
      }
    };
    const watchHandle = watch(source, cb, baseWatchOptions);
    if (isInSSRComponentSetup) {
      if (ssrCleanup) {
        ssrCleanup.push(watchHandle);
      } else if (runsImmediately) {
        watchHandle();
      }
    }
    return watchHandle;
  }
  function instanceWatch(source, value, options) {
    const publicThis = this.proxy;
    const getter = isString(source) ? source.includes(".") ? createPathGetter(publicThis, source) : () => publicThis[source] : source.bind(publicThis, publicThis);
    let cb;
    if (isFunction(value)) {
      cb = value;
    } else {
      cb = value.handler;
      options = value;
    }
    const reset = setCurrentInstance(this);
    const res = doWatch(getter, cb.bind(publicThis), options);
    reset();
    return res;
  }
  function createPathGetter(ctx, path) {
    const segments = path.split(".");
    return () => {
      let cur = ctx;
      for (let i = 0; i < segments.length && cur; i++) {
        cur = cur[segments[i]];
      }
      return cur;
    };
  }
  var getModelModifiers = (props, modelName) => {
    return modelName === "modelValue" || modelName === "model-value" ? props.modelModifiers : props[`${modelName}Modifiers`] || props[`${camelize(modelName)}Modifiers`] || props[`${hyphenate(modelName)}Modifiers`];
  };
  function emit(instance, event, ...rawArgs) {
    if (instance.isUnmounted)
      return;
    const props = instance.vnode.props || EMPTY_OBJ;
    if (true) {
      const {
        emitsOptions,
        propsOptions: [propsOptions]
      } = instance;
      if (emitsOptions) {
        if (!(event in emitsOptions) && true) {
          if (!propsOptions || !(toHandlerKey(camelize(event)) in propsOptions)) {
            warn$1(
              `Component emitted event "${event}" but it is neither declared in the emits option nor as an "${toHandlerKey(camelize(event))}" prop.`
            );
          }
        } else {
          const validator = emitsOptions[event];
          if (isFunction(validator)) {
            const isValid = validator(...rawArgs);
            if (!isValid) {
              warn$1(
                `Invalid event arguments: event validation failed for event "${event}".`
              );
            }
          }
        }
      }
    }
    let args = rawArgs;
    const isModelListener3 = event.startsWith("update:");
    const modifiers = isModelListener3 && getModelModifiers(props, event.slice(7));
    if (modifiers) {
      if (modifiers.trim) {
        args = rawArgs.map((a) => isString(a) ? a.trim() : a);
      }
      if (modifiers.number) {
        args = rawArgs.map(looseToNumber);
      }
    }
    if (true) {
      devtoolsComponentEmit(instance, event, args);
    }
    if (true) {
      const lowerCaseEvent = event.toLowerCase();
      if (lowerCaseEvent !== event && props[toHandlerKey(lowerCaseEvent)]) {
        warn$1(
          `Event "${lowerCaseEvent}" is emitted in component ${formatComponentName(
            instance,
            instance.type
          )} but the handler is registered for "${event}". Note that HTML attributes are case-insensitive and you cannot use v-on to listen to camelCase events when using in-DOM templates. You should probably use "${hyphenate(
            event
          )}" instead of "${event}".`
        );
      }
    }
    let handlerName;
    let handler = props[handlerName = toHandlerKey(event)] || props[handlerName = toHandlerKey(camelize(event))];
    if (!handler && isModelListener3) {
      handler = props[handlerName = toHandlerKey(hyphenate(event))];
    }
    if (handler) {
      callWithAsyncErrorHandling(
        handler,
        instance,
        6,
        args
      );
    }
    const onceHandler = props[handlerName + `Once`];
    if (onceHandler) {
      if (!instance.emitted) {
        instance.emitted = {};
      } else if (instance.emitted[handlerName]) {
        return;
      }
      instance.emitted[handlerName] = true;
      callWithAsyncErrorHandling(
        onceHandler,
        instance,
        6,
        args
      );
    }
  }
  function normalizeEmitsOptions(comp, appContext, asMixin = false) {
    const cache = appContext.emitsCache;
    const cached = cache.get(comp);
    if (cached !== void 0) {
      return cached;
    }
    const raw = comp.emits;
    let normalized = {};
    let hasExtends = false;
    if (!isFunction(comp)) {
      const extendEmits = (raw2) => {
        const normalizedFromExtend = normalizeEmitsOptions(raw2, appContext, true);
        if (normalizedFromExtend) {
          hasExtends = true;
          extend(normalized, normalizedFromExtend);
        }
      };
      if (!asMixin && appContext.mixins.length) {
        appContext.mixins.forEach(extendEmits);
      }
      if (comp.extends) {
        extendEmits(comp.extends);
      }
      if (comp.mixins) {
        comp.mixins.forEach(extendEmits);
      }
    }
    if (!raw && !hasExtends) {
      if (isObject(comp)) {
        cache.set(comp, null);
      }
      return null;
    }
    if (isArray(raw)) {
      raw.forEach((key) => normalized[key] = null);
    } else {
      extend(normalized, raw);
    }
    if (isObject(comp)) {
      cache.set(comp, normalized);
    }
    return normalized;
  }
  function isEmitListener(options, key) {
    if (!options || !isOn(key)) {
      return false;
    }
    key = key.slice(2).replace(/Once$/, "");
    return hasOwn(options, key[0].toLowerCase() + key.slice(1)) || hasOwn(options, hyphenate(key)) || hasOwn(options, key);
  }
  var accessedAttrs = false;
  function markAttrsAccessed() {
    accessedAttrs = true;
  }
  function renderComponentRoot(instance) {
    const {
      type: Component,
      vnode,
      proxy,
      withProxy,
      propsOptions: [propsOptions],
      slots,
      attrs,
      emit: emit2,
      render: render8,
      renderCache,
      props,
      data,
      setupState,
      ctx,
      inheritAttrs
    } = instance;
    const prev = setCurrentRenderingInstance(instance);
    let result;
    let fallthroughAttrs;
    if (true) {
      accessedAttrs = false;
    }
    try {
      if (vnode.shapeFlag & 4) {
        const proxyToUse = withProxy || proxy;
        const thisProxy = setupState.__isScriptSetup ? new Proxy(proxyToUse, {
          get(target, key, receiver) {
            warn$1(
              `Property '${String(
                key
              )}' was accessed via 'this'. Avoid using 'this' in templates.`
            );
            return Reflect.get(target, key, receiver);
          }
        }) : proxyToUse;
        result = normalizeVNode(
          render8.call(
            thisProxy,
            proxyToUse,
            renderCache,
            true ? shallowReadonly(props) : props,
            setupState,
            data,
            ctx
          )
        );
        fallthroughAttrs = attrs;
      } else {
        const render22 = Component;
        if (attrs === props) {
          markAttrsAccessed();
        }
        result = normalizeVNode(
          render22.length > 1 ? render22(
            true ? shallowReadonly(props) : props,
            true ? {
              get attrs() {
                markAttrsAccessed();
                return shallowReadonly(attrs);
              },
              slots,
              emit: emit2
            } : { attrs, slots, emit: emit2 }
          ) : render22(
            true ? shallowReadonly(props) : props,
            null
          )
        );
        fallthroughAttrs = Component.props ? attrs : getFunctionalFallthrough(attrs);
      }
    } catch (err) {
      blockStack.length = 0;
      handleError(err, instance, 1);
      result = createVNode(Comment);
    }
    let root = result;
    let setRoot = void 0;
    if (result.patchFlag > 0 && result.patchFlag & 2048) {
      [root, setRoot] = getChildRoot(result);
    }
    if (fallthroughAttrs && inheritAttrs !== false) {
      const keys = Object.keys(fallthroughAttrs);
      const { shapeFlag } = root;
      if (keys.length) {
        if (shapeFlag & (1 | 6)) {
          if (propsOptions && keys.some(isModelListener)) {
            fallthroughAttrs = filterModelListeners(
              fallthroughAttrs,
              propsOptions
            );
          }
          root = cloneVNode(root, fallthroughAttrs, false, true);
        } else if (!accessedAttrs && root.type !== Comment) {
          const allAttrs = Object.keys(attrs);
          const eventAttrs = [];
          const extraAttrs = [];
          for (let i = 0, l = allAttrs.length; i < l; i++) {
            const key = allAttrs[i];
            if (isOn(key)) {
              if (!isModelListener(key)) {
                eventAttrs.push(key[2].toLowerCase() + key.slice(3));
              }
            } else {
              extraAttrs.push(key);
            }
          }
          if (extraAttrs.length) {
            warn$1(
              `Extraneous non-props attributes (${extraAttrs.join(", ")}) were passed to component but could not be automatically inherited because component renders fragment or text root nodes.`
            );
          }
          if (eventAttrs.length) {
            warn$1(
              `Extraneous non-emits event listeners (${eventAttrs.join(", ")}) were passed to component but could not be automatically inherited because component renders fragment or text root nodes. If the listener is intended to be a component custom event listener only, declare it using the "emits" option.`
            );
          }
        }
      }
    }
    if (vnode.dirs) {
      if (!isElementRoot(root)) {
        warn$1(
          `Runtime directive used on component with non-element root node. The directives will not function as intended.`
        );
      }
      root = cloneVNode(root, null, false, true);
      root.dirs = root.dirs ? root.dirs.concat(vnode.dirs) : vnode.dirs;
    }
    if (vnode.transition) {
      if (!isElementRoot(root)) {
        warn$1(
          `Component inside <Transition> renders non-element root node that cannot be animated.`
        );
      }
      setTransitionHooks(root, vnode.transition);
    }
    if (setRoot) {
      setRoot(root);
    } else {
      result = root;
    }
    setCurrentRenderingInstance(prev);
    return result;
  }
  var getChildRoot = (vnode) => {
    const rawChildren = vnode.children;
    const dynamicChildren = vnode.dynamicChildren;
    const childRoot = filterSingleRoot(rawChildren, false);
    if (!childRoot) {
      return [vnode, void 0];
    } else if (childRoot.patchFlag > 0 && childRoot.patchFlag & 2048) {
      return getChildRoot(childRoot);
    }
    const index = rawChildren.indexOf(childRoot);
    const dynamicIndex = dynamicChildren ? dynamicChildren.indexOf(childRoot) : -1;
    const setRoot = (updatedRoot) => {
      rawChildren[index] = updatedRoot;
      if (dynamicChildren) {
        if (dynamicIndex > -1) {
          dynamicChildren[dynamicIndex] = updatedRoot;
        } else if (updatedRoot.patchFlag > 0) {
          vnode.dynamicChildren = [...dynamicChildren, updatedRoot];
        }
      }
    };
    return [normalizeVNode(childRoot), setRoot];
  };
  function filterSingleRoot(children, recurse = true) {
    let singleRoot;
    for (let i = 0; i < children.length; i++) {
      const child = children[i];
      if (isVNode(child)) {
        if (child.type !== Comment || child.children === "v-if") {
          if (singleRoot) {
            return;
          } else {
            singleRoot = child;
            if (recurse && singleRoot.patchFlag > 0 && singleRoot.patchFlag & 2048) {
              return filterSingleRoot(singleRoot.children);
            }
          }
        }
      } else {
        return;
      }
    }
    return singleRoot;
  }
  var getFunctionalFallthrough = (attrs) => {
    let res;
    for (const key in attrs) {
      if (key === "class" || key === "style" || isOn(key)) {
        (res || (res = {}))[key] = attrs[key];
      }
    }
    return res;
  };
  var filterModelListeners = (attrs, props) => {
    const res = {};
    for (const key in attrs) {
      if (!isModelListener(key) || !(key.slice(9) in props)) {
        res[key] = attrs[key];
      }
    }
    return res;
  };
  var isElementRoot = (vnode) => {
    return vnode.shapeFlag & (6 | 1) || vnode.type === Comment;
  };
  function shouldUpdateComponent(prevVNode, nextVNode, optimized) {
    const { props: prevProps, children: prevChildren, component } = prevVNode;
    const { props: nextProps, children: nextChildren, patchFlag } = nextVNode;
    const emits = component.emitsOptions;
    if ((prevChildren || nextChildren) && isHmrUpdating) {
      return true;
    }
    if (nextVNode.dirs || nextVNode.transition) {
      return true;
    }
    if (optimized && patchFlag >= 0) {
      if (patchFlag & 1024) {
        return true;
      }
      if (patchFlag & 16) {
        if (!prevProps) {
          return !!nextProps;
        }
        return hasPropsChanged(prevProps, nextProps, emits);
      } else if (patchFlag & 8) {
        const dynamicProps = nextVNode.dynamicProps;
        for (let i = 0; i < dynamicProps.length; i++) {
          const key = dynamicProps[i];
          if (nextProps[key] !== prevProps[key] && !isEmitListener(emits, key)) {
            return true;
          }
        }
      }
    } else {
      if (prevChildren || nextChildren) {
        if (!nextChildren || !nextChildren.$stable) {
          return true;
        }
      }
      if (prevProps === nextProps) {
        return false;
      }
      if (!prevProps) {
        return !!nextProps;
      }
      if (!nextProps) {
        return true;
      }
      return hasPropsChanged(prevProps, nextProps, emits);
    }
    return false;
  }
  function hasPropsChanged(prevProps, nextProps, emitsOptions) {
    const nextKeys = Object.keys(nextProps);
    if (nextKeys.length !== Object.keys(prevProps).length) {
      return true;
    }
    for (let i = 0; i < nextKeys.length; i++) {
      const key = nextKeys[i];
      if (nextProps[key] !== prevProps[key] && !isEmitListener(emitsOptions, key)) {
        return true;
      }
    }
    return false;
  }
  function updateHOCHostEl({ vnode, parent }, el) {
    while (parent) {
      const root = parent.subTree;
      if (root.suspense && root.suspense.activeBranch === vnode) {
        root.el = vnode.el;
      }
      if (root === vnode) {
        (vnode = parent.vnode).el = el;
        parent = parent.parent;
      } else {
        break;
      }
    }
  }
  var isSuspense = (type) => type.__isSuspense;
  function queueEffectWithSuspense(fn2, suspense) {
    if (suspense && suspense.pendingBranch) {
      if (isArray(fn2)) {
        suspense.effects.push(...fn2);
      } else {
        suspense.effects.push(fn2);
      }
    } else {
      queuePostFlushCb(fn2);
    }
  }
  var Fragment = Symbol.for("v-fgt");
  var Text = Symbol.for("v-txt");
  var Comment = Symbol.for("v-cmt");
  var Static = Symbol.for("v-stc");
  var blockStack = [];
  var currentBlock = null;
  function openBlock(disableTracking = false) {
    blockStack.push(currentBlock = disableTracking ? null : []);
  }
  function closeBlock() {
    blockStack.pop();
    currentBlock = blockStack[blockStack.length - 1] || null;
  }
  var isBlockTreeEnabled = 1;
  function setBlockTracking(value) {
    isBlockTreeEnabled += value;
    if (value < 0 && currentBlock) {
      currentBlock.hasOnce = true;
    }
  }
  function setupBlock(vnode) {
    vnode.dynamicChildren = isBlockTreeEnabled > 0 ? currentBlock || EMPTY_ARR : null;
    closeBlock();
    if (isBlockTreeEnabled > 0 && currentBlock) {
      currentBlock.push(vnode);
    }
    return vnode;
  }
  function createElementBlock(type, props, children, patchFlag, dynamicProps, shapeFlag) {
    return setupBlock(
      createBaseVNode(
        type,
        props,
        children,
        patchFlag,
        dynamicProps,
        shapeFlag,
        true
      )
    );
  }
  function createBlock(type, props, children, patchFlag, dynamicProps) {
    return setupBlock(
      createVNode(
        type,
        props,
        children,
        patchFlag,
        dynamicProps,
        true
      )
    );
  }
  function isVNode(value) {
    return value ? value.__v_isVNode === true : false;
  }
  function isSameVNodeType(n1, n2) {
    if (n2.shapeFlag & 6 && n1.component) {
      const dirtyInstances = hmrDirtyComponents.get(n2.type);
      if (dirtyInstances && dirtyInstances.has(n1.component)) {
        n1.shapeFlag &= ~256;
        n2.shapeFlag &= ~512;
        return false;
      }
    }
    return n1.type === n2.type && n1.key === n2.key;
  }
  var vnodeArgsTransformer;
  var createVNodeWithArgsTransform = (...args) => {
    return _createVNode(
      ...vnodeArgsTransformer ? vnodeArgsTransformer(args, currentRenderingInstance) : args
    );
  };
  var normalizeKey = ({ key }) => key != null ? key : null;
  var normalizeRef = ({
    ref: ref3,
    ref_key,
    ref_for
  }) => {
    if (typeof ref3 === "number") {
      ref3 = "" + ref3;
    }
    return ref3 != null ? isString(ref3) || isRef2(ref3) || isFunction(ref3) ? { i: currentRenderingInstance, r: ref3, k: ref_key, f: !!ref_for } : ref3 : null;
  };
  function createBaseVNode(type, props = null, children = null, patchFlag = 0, dynamicProps = null, shapeFlag = type === Fragment ? 0 : 1, isBlockNode = false, needFullChildrenNormalization = false) {
    const vnode = {
      __v_isVNode: true,
      __v_skip: true,
      type,
      props,
      key: props && normalizeKey(props),
      ref: props && normalizeRef(props),
      scopeId: currentScopeId,
      slotScopeIds: null,
      children,
      component: null,
      suspense: null,
      ssContent: null,
      ssFallback: null,
      dirs: null,
      transition: null,
      el: null,
      anchor: null,
      target: null,
      targetStart: null,
      targetAnchor: null,
      staticCount: 0,
      shapeFlag,
      patchFlag,
      dynamicProps,
      dynamicChildren: null,
      appContext: null,
      ctx: currentRenderingInstance
    };
    if (needFullChildrenNormalization) {
      normalizeChildren(vnode, children);
      if (shapeFlag & 128) {
        type.normalize(vnode);
      }
    } else if (children) {
      vnode.shapeFlag |= isString(children) ? 8 : 16;
    }
    if (vnode.key !== vnode.key) {
      warn$1(`VNode created with invalid key (NaN). VNode type:`, vnode.type);
    }
    if (isBlockTreeEnabled > 0 && !isBlockNode && currentBlock && (vnode.patchFlag > 0 || shapeFlag & 6) && vnode.patchFlag !== 32) {
      currentBlock.push(vnode);
    }
    return vnode;
  }
  var createVNode = true ? createVNodeWithArgsTransform : _createVNode;
  function _createVNode(type, props = null, children = null, patchFlag = 0, dynamicProps = null, isBlockNode = false) {
    if (!type || type === NULL_DYNAMIC_COMPONENT) {
      if (!type) {
        warn$1(`Invalid vnode type when creating vnode: ${type}.`);
      }
      type = Comment;
    }
    if (isVNode(type)) {
      const cloned = cloneVNode(
        type,
        props,
        true
      );
      if (children) {
        normalizeChildren(cloned, children);
      }
      if (isBlockTreeEnabled > 0 && !isBlockNode && currentBlock) {
        if (cloned.shapeFlag & 6) {
          currentBlock[currentBlock.indexOf(type)] = cloned;
        } else {
          currentBlock.push(cloned);
        }
      }
      cloned.patchFlag = -2;
      return cloned;
    }
    if (isClassComponent(type)) {
      type = type.__vccOpts;
    }
    if (props) {
      props = guardReactiveProps(props);
      let { class: klass, style } = props;
      if (klass && !isString(klass)) {
        props.class = normalizeClass(klass);
      }
      if (isObject(style)) {
        if (isProxy(style) && !isArray(style)) {
          style = extend({}, style);
        }
        props.style = normalizeStyle(style);
      }
    }
    const shapeFlag = isString(type) ? 1 : isSuspense(type) ? 128 : isTeleport(type) ? 64 : isObject(type) ? 4 : isFunction(type) ? 2 : 0;
    if (shapeFlag & 4 && isProxy(type)) {
      type = toRaw(type);
      warn$1(
        `Vue received a Component that was made a reactive object. This can lead to unnecessary performance overhead and should be avoided by marking the component with \`markRaw\` or using \`shallowRef\` instead of \`ref\`.`,
        `
Component that was made reactive: `,
        type
      );
    }
    return createBaseVNode(
      type,
      props,
      children,
      patchFlag,
      dynamicProps,
      shapeFlag,
      isBlockNode,
      true
    );
  }
  function guardReactiveProps(props) {
    if (!props)
      return null;
    return isProxy(props) || isInternalObject(props) ? extend({}, props) : props;
  }
  function cloneVNode(vnode, extraProps, mergeRef = false, cloneTransition = false) {
    const { props, ref: ref3, patchFlag, children, transition } = vnode;
    const mergedProps = extraProps ? mergeProps(props || {}, extraProps) : props;
    const cloned = {
      __v_isVNode: true,
      __v_skip: true,
      type: vnode.type,
      props: mergedProps,
      key: mergedProps && normalizeKey(mergedProps),
      ref: extraProps && extraProps.ref ? mergeRef && ref3 ? isArray(ref3) ? ref3.concat(normalizeRef(extraProps)) : [ref3, normalizeRef(extraProps)] : normalizeRef(extraProps) : ref3,
      scopeId: vnode.scopeId,
      slotScopeIds: vnode.slotScopeIds,
      children: patchFlag === -1 && isArray(children) ? children.map(deepCloneVNode) : children,
      target: vnode.target,
      targetStart: vnode.targetStart,
      targetAnchor: vnode.targetAnchor,
      staticCount: vnode.staticCount,
      shapeFlag: vnode.shapeFlag,
      patchFlag: extraProps && vnode.type !== Fragment ? patchFlag === -1 ? 16 : patchFlag | 16 : patchFlag,
      dynamicProps: vnode.dynamicProps,
      dynamicChildren: vnode.dynamicChildren,
      appContext: vnode.appContext,
      dirs: vnode.dirs,
      transition,
      component: vnode.component,
      suspense: vnode.suspense,
      ssContent: vnode.ssContent && cloneVNode(vnode.ssContent),
      ssFallback: vnode.ssFallback && cloneVNode(vnode.ssFallback),
      el: vnode.el,
      anchor: vnode.anchor,
      ctx: vnode.ctx,
      ce: vnode.ce
    };
    if (transition && cloneTransition) {
      setTransitionHooks(
        cloned,
        transition.clone(cloned)
      );
    }
    return cloned;
  }
  function deepCloneVNode(vnode) {
    const cloned = cloneVNode(vnode);
    if (isArray(vnode.children)) {
      cloned.children = vnode.children.map(deepCloneVNode);
    }
    return cloned;
  }
  function createTextVNode(text = " ", flag = 0) {
    return createVNode(Text, null, text, flag);
  }
  function createStaticVNode(content, numberOfNodes) {
    const vnode = createVNode(Static, null, content);
    vnode.staticCount = numberOfNodes;
    return vnode;
  }
  function createCommentVNode(text = "", asBlock = false) {
    return asBlock ? (openBlock(), createBlock(Comment, null, text)) : createVNode(Comment, null, text);
  }
  function normalizeVNode(child) {
    if (child == null || typeof child === "boolean") {
      return createVNode(Comment);
    } else if (isArray(child)) {
      return createVNode(
        Fragment,
        null,
        child.slice()
      );
    } else if (isVNode(child)) {
      return cloneIfMounted(child);
    } else {
      return createVNode(Text, null, String(child));
    }
  }
  function cloneIfMounted(child) {
    return child.el === null && child.patchFlag !== -1 || child.memo ? child : cloneVNode(child);
  }
  function normalizeChildren(vnode, children) {
    let type = 0;
    const { shapeFlag } = vnode;
    if (children == null) {
      children = null;
    } else if (isArray(children)) {
      type = 16;
    } else if (typeof children === "object") {
      if (shapeFlag & (1 | 64)) {
        const slot = children.default;
        if (slot) {
          slot._c && (slot._d = false);
          normalizeChildren(vnode, slot());
          slot._c && (slot._d = true);
        }
        return;
      } else {
        type = 32;
        const slotFlag = children._;
        if (!slotFlag && !isInternalObject(children)) {
          children._ctx = currentRenderingInstance;
        } else if (slotFlag === 3 && currentRenderingInstance) {
          if (currentRenderingInstance.slots._ === 1) {
            children._ = 1;
          } else {
            children._ = 2;
            vnode.patchFlag |= 1024;
          }
        }
      }
    } else if (isFunction(children)) {
      children = { default: children, _ctx: currentRenderingInstance };
      type = 32;
    } else {
      children = String(children);
      if (shapeFlag & 64) {
        type = 16;
        children = [createTextVNode(children)];
      } else {
        type = 8;
      }
    }
    vnode.children = children;
    vnode.shapeFlag |= type;
  }
  function mergeProps(...args) {
    const ret = {};
    for (let i = 0; i < args.length; i++) {
      const toMerge = args[i];
      for (const key in toMerge) {
        if (key === "class") {
          if (ret.class !== toMerge.class) {
            ret.class = normalizeClass([ret.class, toMerge.class]);
          }
        } else if (key === "style") {
          ret.style = normalizeStyle([ret.style, toMerge.style]);
        } else if (isOn(key)) {
          const existing = ret[key];
          const incoming = toMerge[key];
          if (incoming && existing !== incoming && !(isArray(existing) && existing.includes(incoming))) {
            ret[key] = existing ? [].concat(existing, incoming) : incoming;
          }
        } else if (key !== "") {
          ret[key] = toMerge[key];
        }
      }
    }
    return ret;
  }
  function invokeVNodeHook(hook, instance, vnode, prevVNode = null) {
    callWithAsyncErrorHandling(hook, instance, 7, [
      vnode,
      prevVNode
    ]);
  }
  var emptyAppContext = createAppContext();
  var uid = 0;
  function createComponentInstance(vnode, parent, suspense) {
    const type = vnode.type;
    const appContext = (parent ? parent.appContext : vnode.appContext) || emptyAppContext;
    const instance = {
      uid: uid++,
      vnode,
      type,
      parent,
      appContext,
      root: null,
      next: null,
      subTree: null,
      effect: null,
      update: null,
      job: null,
      scope: new EffectScope(
        true
      ),
      render: null,
      proxy: null,
      exposed: null,
      exposeProxy: null,
      withProxy: null,
      provides: parent ? parent.provides : Object.create(appContext.provides),
      ids: parent ? parent.ids : ["", 0, 0],
      accessCache: null,
      renderCache: [],
      components: null,
      directives: null,
      propsOptions: normalizePropsOptions(type, appContext),
      emitsOptions: normalizeEmitsOptions(type, appContext),
      emit: null,
      emitted: null,
      propsDefaults: EMPTY_OBJ,
      inheritAttrs: type.inheritAttrs,
      ctx: EMPTY_OBJ,
      data: EMPTY_OBJ,
      props: EMPTY_OBJ,
      attrs: EMPTY_OBJ,
      slots: EMPTY_OBJ,
      refs: EMPTY_OBJ,
      setupState: EMPTY_OBJ,
      setupContext: null,
      suspense,
      suspenseId: suspense ? suspense.pendingId : 0,
      asyncDep: null,
      asyncResolved: false,
      isMounted: false,
      isUnmounted: false,
      isDeactivated: false,
      bc: null,
      c: null,
      bm: null,
      m: null,
      bu: null,
      u: null,
      um: null,
      bum: null,
      da: null,
      a: null,
      rtg: null,
      rtc: null,
      ec: null,
      sp: null
    };
    if (true) {
      instance.ctx = createDevRenderContext(instance);
    } else {
      instance.ctx = { _: instance };
    }
    instance.root = parent ? parent.root : instance;
    instance.emit = emit.bind(null, instance);
    if (vnode.ce) {
      vnode.ce(instance);
    }
    return instance;
  }
  var currentInstance = null;
  var getCurrentInstance = () => currentInstance || currentRenderingInstance;
  var internalSetCurrentInstance;
  var setInSSRSetupState;
  {
    const g = getGlobalThis();
    const registerGlobalSetter = (key, setter) => {
      let setters;
      if (!(setters = g[key]))
        setters = g[key] = [];
      setters.push(setter);
      return (v) => {
        if (setters.length > 1)
          setters.forEach((set2) => set2(v));
        else
          setters[0](v);
      };
    };
    internalSetCurrentInstance = registerGlobalSetter(
      `__VUE_INSTANCE_SETTERS__`,
      (v) => currentInstance = v
    );
    setInSSRSetupState = registerGlobalSetter(
      `__VUE_SSR_SETTERS__`,
      (v) => isInSSRComponentSetup = v
    );
  }
  var setCurrentInstance = (instance) => {
    const prev = currentInstance;
    internalSetCurrentInstance(instance);
    instance.scope.on();
    return () => {
      instance.scope.off();
      internalSetCurrentInstance(prev);
    };
  };
  var unsetCurrentInstance = () => {
    currentInstance && currentInstance.scope.off();
    internalSetCurrentInstance(null);
  };
  var isBuiltInTag = /* @__PURE__ */ makeMap("slot,component");
  function validateComponentName(name, { isNativeTag }) {
    if (isBuiltInTag(name) || isNativeTag(name)) {
      warn$1(
        "Do not use built-in or reserved HTML elements as component id: " + name
      );
    }
  }
  function isStatefulComponent(instance) {
    return instance.vnode.shapeFlag & 4;
  }
  var isInSSRComponentSetup = false;
  function setupComponent(instance, isSSR = false, optimized = false) {
    isSSR && setInSSRSetupState(isSSR);
    const { props, children } = instance.vnode;
    const isStateful = isStatefulComponent(instance);
    initProps(instance, props, isStateful, isSSR);
    initSlots(instance, children, optimized);
    const setupResult = isStateful ? setupStatefulComponent(instance, isSSR) : void 0;
    isSSR && setInSSRSetupState(false);
    return setupResult;
  }
  function setupStatefulComponent(instance, isSSR) {
    var _a;
    const Component = instance.type;
    if (true) {
      if (Component.name) {
        validateComponentName(Component.name, instance.appContext.config);
      }
      if (Component.components) {
        const names = Object.keys(Component.components);
        for (let i = 0; i < names.length; i++) {
          validateComponentName(names[i], instance.appContext.config);
        }
      }
      if (Component.directives) {
        const names = Object.keys(Component.directives);
        for (let i = 0; i < names.length; i++) {
          validateDirectiveName(names[i]);
        }
      }
      if (Component.compilerOptions && isRuntimeOnly()) {
        warn$1(
          `"compilerOptions" is only supported when using a build of Vue that includes the runtime compiler. Since you are using a runtime-only build, the options should be passed via your build tool config instead.`
        );
      }
    }
    instance.accessCache = /* @__PURE__ */ Object.create(null);
    instance.proxy = new Proxy(instance.ctx, PublicInstanceProxyHandlers);
    if (true) {
      exposePropsOnRenderContext(instance);
    }
    const { setup } = Component;
    if (setup) {
      pauseTracking();
      const setupContext = instance.setupContext = setup.length > 1 ? createSetupContext(instance) : null;
      const reset = setCurrentInstance(instance);
      const setupResult = callWithErrorHandling(
        setup,
        instance,
        0,
        [
          true ? shallowReadonly(instance.props) : instance.props,
          setupContext
        ]
      );
      const isAsyncSetup = isPromise(setupResult);
      resetTracking();
      reset();
      if ((isAsyncSetup || instance.sp) && !isAsyncWrapper(instance)) {
        markAsyncBoundary(instance);
      }
      if (isAsyncSetup) {
        setupResult.then(unsetCurrentInstance, unsetCurrentInstance);
        if (isSSR) {
          return setupResult.then((resolvedResult) => {
            handleSetupResult(instance, resolvedResult, isSSR);
          }).catch((e) => {
            handleError(e, instance, 0);
          });
        } else {
          instance.asyncDep = setupResult;
          if (!instance.suspense) {
            const name = (_a = Component.name) != null ? _a : "Anonymous";
            warn$1(
              `Component <${name}>: setup function returned a promise, but no <Suspense> boundary was found in the parent component tree. A component with async setup() must be nested in a <Suspense> in order to be rendered.`
            );
          }
        }
      } else {
        handleSetupResult(instance, setupResult, isSSR);
      }
    } else {
      finishComponentSetup(instance, isSSR);
    }
  }
  function handleSetupResult(instance, setupResult, isSSR) {
    if (isFunction(setupResult)) {
      if (instance.type.__ssrInlineRender) {
        instance.ssrRender = setupResult;
      } else {
        instance.render = setupResult;
      }
    } else if (isObject(setupResult)) {
      if (isVNode(setupResult)) {
        warn$1(
          `setup() should not return VNodes directly - return a render function instead.`
        );
      }
      if (true) {
        instance.devtoolsRawSetupState = setupResult;
      }
      instance.setupState = proxyRefs(setupResult);
      if (true) {
        exposeSetupStateOnRenderContext(instance);
      }
    } else if (setupResult !== void 0) {
      warn$1(
        `setup() should return an object. Received: ${setupResult === null ? "null" : typeof setupResult}`
      );
    }
    finishComponentSetup(instance, isSSR);
  }
  var compile;
  var installWithProxy;
  var isRuntimeOnly = () => !compile;
  function finishComponentSetup(instance, isSSR, skipOptions) {
    const Component = instance.type;
    if (!instance.render) {
      if (!isSSR && compile && !Component.render) {
        const template = Component.template || resolveMergedOptions(instance).template;
        if (template) {
          if (true) {
            startMeasure(instance, `compile`);
          }
          const { isCustomElement, compilerOptions } = instance.appContext.config;
          const { delimiters, compilerOptions: componentCompilerOptions } = Component;
          const finalCompilerOptions = extend(
            extend(
              {
                isCustomElement,
                delimiters
              },
              compilerOptions
            ),
            componentCompilerOptions
          );
          Component.render = compile(template, finalCompilerOptions);
          if (true) {
            endMeasure(instance, `compile`);
          }
        }
      }
      instance.render = Component.render || NOOP;
      if (installWithProxy) {
        installWithProxy(instance);
      }
    }
    if (true) {
      const reset = setCurrentInstance(instance);
      pauseTracking();
      try {
        applyOptions(instance);
      } finally {
        resetTracking();
        reset();
      }
    }
    if (!Component.render && instance.render === NOOP && !isSSR) {
      if (!compile && Component.template) {
        warn$1(
          `Component provided template option but runtime compilation is not supported in this build of Vue. Configure your bundler to alias "vue" to "vue/dist/vue.esm-bundler.js".`
        );
      } else {
        warn$1(`Component is missing template or render function: `, Component);
      }
    }
  }
  var attrsProxyHandlers = true ? {
    get(target, key) {
      markAttrsAccessed();
      track(target, "get", "");
      return target[key];
    },
    set() {
      warn$1(`setupContext.attrs is readonly.`);
      return false;
    },
    deleteProperty() {
      warn$1(`setupContext.attrs is readonly.`);
      return false;
    }
  } : {
    get(target, key) {
      track(target, "get", "");
      return target[key];
    }
  };
  function getSlotsProxy(instance) {
    return new Proxy(instance.slots, {
      get(target, key) {
        track(instance, "get", "$slots");
        return target[key];
      }
    });
  }
  function createSetupContext(instance) {
    const expose = (exposed) => {
      if (true) {
        if (instance.exposed) {
          warn$1(`expose() should be called only once per setup().`);
        }
        if (exposed != null) {
          let exposedType = typeof exposed;
          if (exposedType === "object") {
            if (isArray(exposed)) {
              exposedType = "array";
            } else if (isRef2(exposed)) {
              exposedType = "ref";
            }
          }
          if (exposedType !== "object") {
            warn$1(
              `expose() should be passed a plain object, received ${exposedType}.`
            );
          }
        }
      }
      instance.exposed = exposed || {};
    };
    if (true) {
      let attrsProxy;
      let slotsProxy;
      return Object.freeze({
        get attrs() {
          return attrsProxy || (attrsProxy = new Proxy(instance.attrs, attrsProxyHandlers));
        },
        get slots() {
          return slotsProxy || (slotsProxy = getSlotsProxy(instance));
        },
        get emit() {
          return (event, ...args) => instance.emit(event, ...args);
        },
        expose
      });
    } else {
      return {
        attrs: new Proxy(instance.attrs, attrsProxyHandlers),
        slots: instance.slots,
        emit: instance.emit,
        expose
      };
    }
  }
  function getComponentPublicInstance(instance) {
    if (instance.exposed) {
      return instance.exposeProxy || (instance.exposeProxy = new Proxy(proxyRefs(markRaw(instance.exposed)), {
        get(target, key) {
          if (key in target) {
            return target[key];
          } else if (key in publicPropertiesMap) {
            return publicPropertiesMap[key](instance);
          }
        },
        has(target, key) {
          return key in target || key in publicPropertiesMap;
        }
      }));
    } else {
      return instance.proxy;
    }
  }
  var classifyRE = /(?:^|[-_])(\w)/g;
  var classify = (str) => str.replace(classifyRE, (c) => c.toUpperCase()).replace(/[-_]/g, "");
  function getComponentName(Component, includeInferred = true) {
    return isFunction(Component) ? Component.displayName || Component.name : Component.name || includeInferred && Component.__name;
  }
  function formatComponentName(instance, Component, isRoot = false) {
    let name = getComponentName(Component);
    if (!name && Component.__file) {
      const match = Component.__file.match(/([^/\\]+)\.\w+$/);
      if (match) {
        name = match[1];
      }
    }
    if (!name && instance && instance.parent) {
      const inferFromRegistry = (registry) => {
        for (const key in registry) {
          if (registry[key] === Component) {
            return key;
          }
        }
      };
      name = inferFromRegistry(
        instance.components || instance.parent.type.components
      ) || inferFromRegistry(instance.appContext.components);
    }
    return name ? classify(name) : isRoot ? `App` : `Anonymous`;
  }
  function isClassComponent(value) {
    return isFunction(value) && "__vccOpts" in value;
  }
  var computed2 = (getterOrOptions, debugOptions) => {
    const c = computed(getterOrOptions, debugOptions, isInSSRComponentSetup);
    if (true) {
      const i = getCurrentInstance();
      if (i && i.appContext.config.warnRecursiveComputed) {
        c._warnRecursive = true;
      }
    }
    return c;
  };
  function initCustomFormatter() {
    if (typeof window === "undefined") {
      return;
    }
    const vueStyle = { style: "color:#3ba776" };
    const numberStyle = { style: "color:#1677ff" };
    const stringStyle = { style: "color:#f5222d" };
    const keywordStyle = { style: "color:#eb2f96" };
    const formatter = {
      __vue_custom_formatter: true,
      header(obj) {
        if (!isObject(obj)) {
          return null;
        }
        if (obj.__isVue) {
          return ["div", vueStyle, `VueInstance`];
        } else if (isRef2(obj)) {
          return [
            "div",
            {},
            ["span", vueStyle, genRefFlag(obj)],
            "<",
            formatValue("_value" in obj ? obj._value : obj),
            `>`
          ];
        } else if (isReactive(obj)) {
          return [
            "div",
            {},
            ["span", vueStyle, isShallow(obj) ? "ShallowReactive" : "Reactive"],
            "<",
            formatValue(obj),
            `>${isReadonly(obj) ? ` (readonly)` : ``}`
          ];
        } else if (isReadonly(obj)) {
          return [
            "div",
            {},
            ["span", vueStyle, isShallow(obj) ? "ShallowReadonly" : "Readonly"],
            "<",
            formatValue(obj),
            ">"
          ];
        }
        return null;
      },
      hasBody(obj) {
        return obj && obj.__isVue;
      },
      body(obj) {
        if (obj && obj.__isVue) {
          return [
            "div",
            {},
            ...formatInstance(obj.$)
          ];
        }
      }
    };
    function formatInstance(instance) {
      const blocks = [];
      if (instance.type.props && instance.props) {
        blocks.push(createInstanceBlock("props", toRaw(instance.props)));
      }
      if (instance.setupState !== EMPTY_OBJ) {
        blocks.push(createInstanceBlock("setup", instance.setupState));
      }
      if (instance.data !== EMPTY_OBJ) {
        blocks.push(createInstanceBlock("data", toRaw(instance.data)));
      }
      const computed5 = extractKeys(instance, "computed");
      if (computed5) {
        blocks.push(createInstanceBlock("computed", computed5));
      }
      const injected = extractKeys(instance, "inject");
      if (injected) {
        blocks.push(createInstanceBlock("injected", injected));
      }
      blocks.push([
        "div",
        {},
        [
          "span",
          {
            style: keywordStyle.style + ";opacity:0.66"
          },
          "$ (internal): "
        ],
        ["object", { object: instance }]
      ]);
      return blocks;
    }
    function createInstanceBlock(type, target) {
      target = extend({}, target);
      if (!Object.keys(target).length) {
        return ["span", {}];
      }
      return [
        "div",
        { style: "line-height:1.25em;margin-bottom:0.6em" },
        [
          "div",
          {
            style: "color:#476582"
          },
          type
        ],
        [
          "div",
          {
            style: "padding-left:1.25em"
          },
          ...Object.keys(target).map((key) => {
            return [
              "div",
              {},
              ["span", keywordStyle, key + ": "],
              formatValue(target[key], false)
            ];
          })
        ]
      ];
    }
    function formatValue(v, asRaw = true) {
      if (typeof v === "number") {
        return ["span", numberStyle, v];
      } else if (typeof v === "string") {
        return ["span", stringStyle, JSON.stringify(v)];
      } else if (typeof v === "boolean") {
        return ["span", keywordStyle, v];
      } else if (isObject(v)) {
        return ["object", { object: asRaw ? toRaw(v) : v }];
      } else {
        return ["span", stringStyle, String(v)];
      }
    }
    function extractKeys(instance, type) {
      const Comp = instance.type;
      if (isFunction(Comp)) {
        return;
      }
      const extracted = {};
      for (const key in instance.ctx) {
        if (isKeyOfType(Comp, key, type)) {
          extracted[key] = instance.ctx[key];
        }
      }
      return extracted;
    }
    function isKeyOfType(Comp, key, type) {
      const opts = Comp[type];
      if (isArray(opts) && opts.includes(key) || isObject(opts) && key in opts) {
        return true;
      }
      if (Comp.extends && isKeyOfType(Comp.extends, key, type)) {
        return true;
      }
      if (Comp.mixins && Comp.mixins.some((m) => isKeyOfType(m, key, type))) {
        return true;
      }
    }
    function genRefFlag(v) {
      if (isShallow(v)) {
        return `ShallowRef`;
      }
      if (v.effect) {
        return `ComputedRef`;
      }
      return `Ref`;
    }
    if (window.devtoolsFormatters) {
      window.devtoolsFormatters.push(formatter);
    } else {
      window.devtoolsFormatters = [formatter];
    }
  }
  var version = "3.5.12";
  var warn2 = true ? warn$1 : NOOP;

  // ../powerpro/node_modules/@vue/runtime-dom/dist/runtime-dom.esm-bundler.js
  var policy = void 0;
  var tt = typeof window !== "undefined" && window.trustedTypes;
  if (tt) {
    try {
      policy = /* @__PURE__ */ tt.createPolicy("vue", {
        createHTML: (val) => val
      });
    } catch (e) {
      warn2(`Error creating trusted types policy: ${e}`);
    }
  }
  var unsafeToTrustedHTML = policy ? (val) => policy.createHTML(val) : (val) => val;
  var svgNS = "http://www.w3.org/2000/svg";
  var mathmlNS = "http://www.w3.org/1998/Math/MathML";
  var doc = typeof document !== "undefined" ? document : null;
  var templateContainer = doc && /* @__PURE__ */ doc.createElement("template");
  var nodeOps = {
    insert: (child, parent, anchor) => {
      parent.insertBefore(child, anchor || null);
    },
    remove: (child) => {
      const parent = child.parentNode;
      if (parent) {
        parent.removeChild(child);
      }
    },
    createElement: (tag, namespace, is, props) => {
      const el = namespace === "svg" ? doc.createElementNS(svgNS, tag) : namespace === "mathml" ? doc.createElementNS(mathmlNS, tag) : is ? doc.createElement(tag, { is }) : doc.createElement(tag);
      if (tag === "select" && props && props.multiple != null) {
        el.setAttribute("multiple", props.multiple);
      }
      return el;
    },
    createText: (text) => doc.createTextNode(text),
    createComment: (text) => doc.createComment(text),
    setText: (node, text) => {
      node.nodeValue = text;
    },
    setElementText: (el, text) => {
      el.textContent = text;
    },
    parentNode: (node) => node.parentNode,
    nextSibling: (node) => node.nextSibling,
    querySelector: (selector) => doc.querySelector(selector),
    setScopeId(el, id) {
      el.setAttribute(id, "");
    },
    insertStaticContent(content, parent, anchor, namespace, start2, end2) {
      const before = anchor ? anchor.previousSibling : parent.lastChild;
      if (start2 && (start2 === end2 || start2.nextSibling)) {
        while (true) {
          parent.insertBefore(start2.cloneNode(true), anchor);
          if (start2 === end2 || !(start2 = start2.nextSibling))
            break;
        }
      } else {
        templateContainer.innerHTML = unsafeToTrustedHTML(
          namespace === "svg" ? `<svg>${content}</svg>` : namespace === "mathml" ? `<math>${content}</math>` : content
        );
        const template = templateContainer.content;
        if (namespace === "svg" || namespace === "mathml") {
          const wrapper = template.firstChild;
          while (wrapper.firstChild) {
            template.appendChild(wrapper.firstChild);
          }
          template.removeChild(wrapper);
        }
        parent.insertBefore(template, anchor);
      }
      return [
        before ? before.nextSibling : parent.firstChild,
        anchor ? anchor.previousSibling : parent.lastChild
      ];
    }
  };
  var vtcKey = Symbol("_vtc");
  function patchClass(el, value, isSVG) {
    const transitionClasses = el[vtcKey];
    if (transitionClasses) {
      value = (value ? [value, ...transitionClasses] : [...transitionClasses]).join(" ");
    }
    if (value == null) {
      el.removeAttribute("class");
    } else if (isSVG) {
      el.setAttribute("class", value);
    } else {
      el.className = value;
    }
  }
  var vShowOriginalDisplay = Symbol("_vod");
  var vShowHidden = Symbol("_vsh");
  var vShow = {
    beforeMount(el, { value }, { transition }) {
      el[vShowOriginalDisplay] = el.style.display === "none" ? "" : el.style.display;
      if (transition && value) {
        transition.beforeEnter(el);
      } else {
        setDisplay(el, value);
      }
    },
    mounted(el, { value }, { transition }) {
      if (transition && value) {
        transition.enter(el);
      }
    },
    updated(el, { value, oldValue }, { transition }) {
      if (!value === !oldValue)
        return;
      if (transition) {
        if (value) {
          transition.beforeEnter(el);
          setDisplay(el, true);
          transition.enter(el);
        } else {
          transition.leave(el, () => {
            setDisplay(el, false);
          });
        }
      } else {
        setDisplay(el, value);
      }
    },
    beforeUnmount(el, { value }) {
      setDisplay(el, value);
    }
  };
  if (true) {
    vShow.name = "show";
  }
  function setDisplay(el, value) {
    el.style.display = value ? el[vShowOriginalDisplay] : "none";
    el[vShowHidden] = !value;
  }
  var CSS_VAR_TEXT = Symbol(true ? "CSS_VAR_TEXT" : "");
  var displayRE = /(^|;)\s*display\s*:/;
  function patchStyle(el, prev, next) {
    const style = el.style;
    const isCssString = isString(next);
    let hasControlledDisplay = false;
    if (next && !isCssString) {
      if (prev) {
        if (!isString(prev)) {
          for (const key in prev) {
            if (next[key] == null) {
              setStyle(style, key, "");
            }
          }
        } else {
          for (const prevStyle of prev.split(";")) {
            const key = prevStyle.slice(0, prevStyle.indexOf(":")).trim();
            if (next[key] == null) {
              setStyle(style, key, "");
            }
          }
        }
      }
      for (const key in next) {
        if (key === "display") {
          hasControlledDisplay = true;
        }
        setStyle(style, key, next[key]);
      }
    } else {
      if (isCssString) {
        if (prev !== next) {
          const cssVarText = style[CSS_VAR_TEXT];
          if (cssVarText) {
            next += ";" + cssVarText;
          }
          style.cssText = next;
          hasControlledDisplay = displayRE.test(next);
        }
      } else if (prev) {
        el.removeAttribute("style");
      }
    }
    if (vShowOriginalDisplay in el) {
      el[vShowOriginalDisplay] = hasControlledDisplay ? style.display : "";
      if (el[vShowHidden]) {
        style.display = "none";
      }
    }
  }
  var semicolonRE = /[^\\];\s*$/;
  var importantRE = /\s*!important$/;
  function setStyle(style, name, val) {
    if (isArray(val)) {
      val.forEach((v) => setStyle(style, name, v));
    } else {
      if (val == null)
        val = "";
      if (true) {
        if (semicolonRE.test(val)) {
          warn2(
            `Unexpected semicolon at the end of '${name}' style value: '${val}'`
          );
        }
      }
      if (name.startsWith("--")) {
        style.setProperty(name, val);
      } else {
        const prefixed = autoPrefix(style, name);
        if (importantRE.test(val)) {
          style.setProperty(
            hyphenate(prefixed),
            val.replace(importantRE, ""),
            "important"
          );
        } else {
          style[prefixed] = val;
        }
      }
    }
  }
  var prefixes = ["Webkit", "Moz", "ms"];
  var prefixCache = {};
  function autoPrefix(style, rawName) {
    const cached = prefixCache[rawName];
    if (cached) {
      return cached;
    }
    let name = camelize(rawName);
    if (name !== "filter" && name in style) {
      return prefixCache[rawName] = name;
    }
    name = capitalize(name);
    for (let i = 0; i < prefixes.length; i++) {
      const prefixed = prefixes[i] + name;
      if (prefixed in style) {
        return prefixCache[rawName] = prefixed;
      }
    }
    return rawName;
  }
  var xlinkNS = "http://www.w3.org/1999/xlink";
  function patchAttr(el, key, value, isSVG, instance, isBoolean2 = isSpecialBooleanAttr(key)) {
    if (isSVG && key.startsWith("xlink:")) {
      if (value == null) {
        el.removeAttributeNS(xlinkNS, key.slice(6, key.length));
      } else {
        el.setAttributeNS(xlinkNS, key, value);
      }
    } else {
      if (value == null || isBoolean2 && !includeBooleanAttr(value)) {
        el.removeAttribute(key);
      } else {
        el.setAttribute(
          key,
          isBoolean2 ? "" : isSymbol(value) ? String(value) : value
        );
      }
    }
  }
  function patchDOMProp(el, key, value, parentComponent, attrName) {
    if (key === "innerHTML" || key === "textContent") {
      if (value != null) {
        el[key] = key === "innerHTML" ? unsafeToTrustedHTML(value) : value;
      }
      return;
    }
    const tag = el.tagName;
    if (key === "value" && tag !== "PROGRESS" && !tag.includes("-")) {
      const oldValue = tag === "OPTION" ? el.getAttribute("value") || "" : el.value;
      const newValue = value == null ? el.type === "checkbox" ? "on" : "" : String(value);
      if (oldValue !== newValue || !("_value" in el)) {
        el.value = newValue;
      }
      if (value == null) {
        el.removeAttribute(key);
      }
      el._value = value;
      return;
    }
    let needRemove = false;
    if (value === "" || value == null) {
      const type = typeof el[key];
      if (type === "boolean") {
        value = includeBooleanAttr(value);
      } else if (value == null && type === "string") {
        value = "";
        needRemove = true;
      } else if (type === "number") {
        value = 0;
        needRemove = true;
      }
    }
    try {
      el[key] = value;
    } catch (e) {
      if (!needRemove) {
        warn2(
          `Failed setting prop "${key}" on <${tag.toLowerCase()}>: value ${value} is invalid.`,
          e
        );
      }
    }
    needRemove && el.removeAttribute(attrName || key);
  }
  function addEventListener(el, event, handler, options) {
    el.addEventListener(event, handler, options);
  }
  function removeEventListener(el, event, handler, options) {
    el.removeEventListener(event, handler, options);
  }
  var veiKey = Symbol("_vei");
  function patchEvent(el, rawName, prevValue, nextValue, instance = null) {
    const invokers = el[veiKey] || (el[veiKey] = {});
    const existingInvoker = invokers[rawName];
    if (nextValue && existingInvoker) {
      existingInvoker.value = true ? sanitizeEventValue(nextValue, rawName) : nextValue;
    } else {
      const [name, options] = parseName(rawName);
      if (nextValue) {
        const invoker = invokers[rawName] = createInvoker(
          true ? sanitizeEventValue(nextValue, rawName) : nextValue,
          instance
        );
        addEventListener(el, name, invoker, options);
      } else if (existingInvoker) {
        removeEventListener(el, name, existingInvoker, options);
        invokers[rawName] = void 0;
      }
    }
  }
  var optionsModifierRE = /(?:Once|Passive|Capture)$/;
  function parseName(name) {
    let options;
    if (optionsModifierRE.test(name)) {
      options = {};
      let m;
      while (m = name.match(optionsModifierRE)) {
        name = name.slice(0, name.length - m[0].length);
        options[m[0].toLowerCase()] = true;
      }
    }
    const event = name[2] === ":" ? name.slice(3) : hyphenate(name.slice(2));
    return [event, options];
  }
  var cachedNow = 0;
  var p = /* @__PURE__ */ Promise.resolve();
  var getNow = () => cachedNow || (p.then(() => cachedNow = 0), cachedNow = Date.now());
  function createInvoker(initialValue, instance) {
    const invoker = (e) => {
      if (!e._vts) {
        e._vts = Date.now();
      } else if (e._vts <= invoker.attached) {
        return;
      }
      callWithAsyncErrorHandling(
        patchStopImmediatePropagation(e, invoker.value),
        instance,
        5,
        [e]
      );
    };
    invoker.value = initialValue;
    invoker.attached = getNow();
    return invoker;
  }
  function sanitizeEventValue(value, propName) {
    if (isFunction(value) || isArray(value)) {
      return value;
    }
    warn2(
      `Wrong type passed as event handler to ${propName} - did you forget @ or : in front of your prop?
Expected function or array of functions, received type ${typeof value}.`
    );
    return NOOP;
  }
  function patchStopImmediatePropagation(e, value) {
    if (isArray(value)) {
      const originalStop = e.stopImmediatePropagation;
      e.stopImmediatePropagation = () => {
        originalStop.call(e);
        e._stopped = true;
      };
      return value.map(
        (fn2) => (e2) => !e2._stopped && fn2 && fn2(e2)
      );
    } else {
      return value;
    }
  }
  var isNativeOn = (key) => key.charCodeAt(0) === 111 && key.charCodeAt(1) === 110 && key.charCodeAt(2) > 96 && key.charCodeAt(2) < 123;
  var patchProp = (el, key, prevValue, nextValue, namespace, parentComponent) => {
    const isSVG = namespace === "svg";
    if (key === "class") {
      patchClass(el, nextValue, isSVG);
    } else if (key === "style") {
      patchStyle(el, prevValue, nextValue);
    } else if (isOn(key)) {
      if (!isModelListener(key)) {
        patchEvent(el, key, prevValue, nextValue, parentComponent);
      }
    } else if (key[0] === "." ? (key = key.slice(1), true) : key[0] === "^" ? (key = key.slice(1), false) : shouldSetAsProp(el, key, nextValue, isSVG)) {
      patchDOMProp(el, key, nextValue);
      if (!el.tagName.includes("-") && (key === "value" || key === "checked" || key === "selected")) {
        patchAttr(el, key, nextValue, isSVG, parentComponent, key !== "value");
      }
    } else if (el._isVueCE && (/[A-Z]/.test(key) || !isString(nextValue))) {
      patchDOMProp(el, camelize(key), nextValue, parentComponent, key);
    } else {
      if (key === "true-value") {
        el._trueValue = nextValue;
      } else if (key === "false-value") {
        el._falseValue = nextValue;
      }
      patchAttr(el, key, nextValue, isSVG);
    }
  };
  function shouldSetAsProp(el, key, value, isSVG) {
    if (isSVG) {
      if (key === "innerHTML" || key === "textContent") {
        return true;
      }
      if (key in el && isNativeOn(key) && isFunction(value)) {
        return true;
      }
      return false;
    }
    if (key === "spellcheck" || key === "draggable" || key === "translate") {
      return false;
    }
    if (key === "form") {
      return false;
    }
    if (key === "list" && el.tagName === "INPUT") {
      return false;
    }
    if (key === "type" && el.tagName === "TEXTAREA") {
      return false;
    }
    if (key === "width" || key === "height") {
      const tag = el.tagName;
      if (tag === "IMG" || tag === "VIDEO" || tag === "CANVAS" || tag === "SOURCE") {
        return false;
      }
    }
    if (isNativeOn(key) && isString(value)) {
      return false;
    }
    return key in el;
  }
  var moveCbKey = Symbol("_moveCb");
  var enterCbKey2 = Symbol("_enterCb");
  var assignKey = Symbol("_assign");
  var systemModifiers = ["ctrl", "shift", "alt", "meta"];
  var modifierGuards = {
    stop: (e) => e.stopPropagation(),
    prevent: (e) => e.preventDefault(),
    self: (e) => e.target !== e.currentTarget,
    ctrl: (e) => !e.ctrlKey,
    shift: (e) => !e.shiftKey,
    alt: (e) => !e.altKey,
    meta: (e) => !e.metaKey,
    left: (e) => "button" in e && e.button !== 0,
    middle: (e) => "button" in e && e.button !== 1,
    right: (e) => "button" in e && e.button !== 2,
    exact: (e, modifiers) => systemModifiers.some((m) => e[`${m}Key`] && !modifiers.includes(m))
  };
  var withModifiers = (fn2, modifiers) => {
    const cache = fn2._withMods || (fn2._withMods = {});
    const cacheKey = modifiers.join(".");
    return cache[cacheKey] || (cache[cacheKey] = (event, ...args) => {
      for (let i = 0; i < modifiers.length; i++) {
        const guard = modifierGuards[modifiers[i]];
        if (guard && guard(event, modifiers))
          return;
      }
      return fn2(event, ...args);
    });
  };
  var rendererOptions = /* @__PURE__ */ extend({ patchProp }, nodeOps);
  var renderer;
  function ensureRenderer() {
    return renderer || (renderer = createRenderer(rendererOptions));
  }
  var createApp = (...args) => {
    const app = ensureRenderer().createApp(...args);
    if (true) {
      injectNativeTagCheck(app);
      injectCompilerOptionsCheck(app);
    }
    const { mount } = app;
    app.mount = (containerOrSelector) => {
      const container = normalizeContainer(containerOrSelector);
      if (!container)
        return;
      const component = app._component;
      if (!isFunction(component) && !component.render && !component.template) {
        component.template = container.innerHTML;
      }
      if (container.nodeType === 1) {
        container.textContent = "";
      }
      const proxy = mount(container, false, resolveRootNamespace(container));
      if (container instanceof Element) {
        container.removeAttribute("v-cloak");
        container.setAttribute("data-v-app", "");
      }
      return proxy;
    };
    return app;
  };
  function resolveRootNamespace(container) {
    if (container instanceof SVGElement) {
      return "svg";
    }
    if (typeof MathMLElement === "function" && container instanceof MathMLElement) {
      return "mathml";
    }
  }
  function injectNativeTagCheck(app) {
    Object.defineProperty(app.config, "isNativeTag", {
      value: (tag) => isHTMLTag(tag) || isSVGTag(tag) || isMathMLTag(tag),
      writable: false
    });
  }
  function injectCompilerOptionsCheck(app) {
    if (isRuntimeOnly()) {
      const isCustomElement = app.config.isCustomElement;
      Object.defineProperty(app.config, "isCustomElement", {
        get() {
          return isCustomElement;
        },
        set() {
          warn2(
            `The \`isCustomElement\` config option is deprecated. Use \`compilerOptions.isCustomElement\` instead.`
          );
        }
      });
      const compilerOptions = app.config.compilerOptions;
      const msg = `The \`compilerOptions\` config option is only respected when using a build of Vue.js that includes the runtime compiler (aka "full build"). Since you are using the runtime-only build, \`compilerOptions\` must be passed to \`@vue/compiler-dom\` in the build setup instead.
- For vue-loader: pass it via vue-loader's \`compilerOptions\` loader option.
- For vue-cli: see https://cli.vuejs.org/guide/webpack.html#modifying-options-of-a-loader
- For vite: pass it via @vitejs/plugin-vue options. See https://github.com/vitejs/vite-plugin-vue/tree/main/packages/plugin-vue#example-for-passing-options-to-vuecompiler-sfc`;
      Object.defineProperty(app.config, "compilerOptions", {
        get() {
          warn2(msg);
          return compilerOptions;
        },
        set() {
          warn2(msg);
        }
      });
    }
  }
  function normalizeContainer(container) {
    if (isString(container)) {
      const res = document.querySelector(container);
      if (!res) {
        warn2(
          `Failed to mount app: mount target selector "${container}" returned null.`
        );
      }
      return res;
    }
    if (window.ShadowRoot && container instanceof window.ShadowRoot && container.mode === "closed") {
      warn2(
        `mounting on a ShadowRoot with \`{mode: "closed"}\` may lead to unpredictable bugs`
      );
    }
    return container;
  }

  // ../powerpro/node_modules/vue/dist/vue.runtime.esm-bundler.js
  function initDev() {
    {
      initCustomFormatter();
    }
  }
  if (true) {
    initDev();
  }

  // node_modules/@vue/shared/dist/shared.esm-bundler.js
  function makeMap2(str, expectsLowerCase) {
    const map3 = /* @__PURE__ */ Object.create(null);
    const list = str.split(",");
    for (let i = 0; i < list.length; i++) {
      map3[list[i]] = true;
    }
    return expectsLowerCase ? (val) => !!map3[val.toLowerCase()] : (val) => !!map3[val];
  }
  var EMPTY_OBJ2 = true ? Object.freeze({}) : {};
  var EMPTY_ARR2 = true ? Object.freeze([]) : [];
  var NOOP2 = () => {
  };
  var NO2 = () => false;
  var onRE = /^on[^a-z]/;
  var isOn2 = (key) => onRE.test(key);
  var extend2 = Object.assign;
  var remove2 = (arr, el) => {
    const i = arr.indexOf(el);
    if (i > -1) {
      arr.splice(i, 1);
    }
  };
  var hasOwnProperty3 = Object.prototype.hasOwnProperty;
  var hasOwn2 = (val, key) => hasOwnProperty3.call(val, key);
  var isArray2 = Array.isArray;
  var isMap2 = (val) => toTypeString2(val) === "[object Map]";
  var isSet2 = (val) => toTypeString2(val) === "[object Set]";
  var isFunction2 = (val) => typeof val === "function";
  var isString2 = (val) => typeof val === "string";
  var isSymbol2 = (val) => typeof val === "symbol";
  var isObject2 = (val) => val !== null && typeof val === "object";
  var isPromise2 = (val) => {
    return (isObject2(val) || isFunction2(val)) && isFunction2(val.then) && isFunction2(val.catch);
  };
  var objectToString2 = Object.prototype.toString;
  var toTypeString2 = (value) => objectToString2.call(value);
  var toRawType2 = (value) => {
    return toTypeString2(value).slice(8, -1);
  };
  var isPlainObject2 = (val) => toTypeString2(val) === "[object Object]";
  var isIntegerKey2 = (key) => isString2(key) && key !== "NaN" && key[0] !== "-" && "" + parseInt(key, 10) === key;
  var cacheStringFunction2 = (fn2) => {
    const cache = /* @__PURE__ */ Object.create(null);
    return (str) => {
      const hit = cache[str];
      return hit || (cache[str] = fn2(str));
    };
  };
  var camelizeRE2 = /-(\w)/g;
  var camelize2 = cacheStringFunction2((str) => {
    return str.replace(camelizeRE2, (_, c) => c ? c.toUpperCase() : "");
  });
  var hyphenateRE2 = /\B([A-Z])/g;
  var hyphenate2 = cacheStringFunction2(
    (str) => str.replace(hyphenateRE2, "-$1").toLowerCase()
  );
  var capitalize2 = cacheStringFunction2((str) => {
    return str.charAt(0).toUpperCase() + str.slice(1);
  });
  var toHandlerKey2 = cacheStringFunction2((str) => {
    const s = str ? `on${capitalize2(str)}` : ``;
    return s;
  });
  var hasChanged2 = (value, oldValue) => !Object.is(value, oldValue);
  var invokeArrayFns2 = (fns, arg) => {
    for (let i = 0; i < fns.length; i++) {
      fns[i](arg);
    }
  };
  var def2 = (obj, key, value) => {
    Object.defineProperty(obj, key, {
      configurable: true,
      enumerable: false,
      value
    });
  };
  var looseToNumber2 = (val) => {
    const n = parseFloat(val);
    return isNaN(n) ? val : n;
  };
  var toNumber2 = (val) => {
    const n = isString2(val) ? Number(val) : NaN;
    return isNaN(n) ? val : n;
  };
  var _globalThis2;
  var getGlobalThis2 = () => {
    return _globalThis2 || (_globalThis2 = typeof globalThis !== "undefined" ? globalThis : typeof self !== "undefined" ? self : typeof window !== "undefined" ? window : typeof global !== "undefined" ? global : {});
  };
  function normalizeStyle2(value) {
    if (isArray2(value)) {
      const res = {};
      for (let i = 0; i < value.length; i++) {
        const item = value[i];
        const normalized = isString2(item) ? parseStringStyle2(item) : normalizeStyle2(item);
        if (normalized) {
          for (const key in normalized) {
            res[key] = normalized[key];
          }
        }
      }
      return res;
    } else if (isString2(value) || isObject2(value)) {
      return value;
    }
  }
  var listDelimiterRE2 = /;(?![^(]*\))/g;
  var propertyDelimiterRE2 = /:([^]+)/;
  var styleCommentRE2 = /\/\*[^]*?\*\//g;
  function parseStringStyle2(cssText) {
    const ret = {};
    cssText.replace(styleCommentRE2, "").split(listDelimiterRE2).forEach((item) => {
      if (item) {
        const tmp = item.split(propertyDelimiterRE2);
        tmp.length > 1 && (ret[tmp[0].trim()] = tmp[1].trim());
      }
    });
    return ret;
  }
  function normalizeClass2(value) {
    let res = "";
    if (isString2(value)) {
      res = value;
    } else if (isArray2(value)) {
      for (let i = 0; i < value.length; i++) {
        const normalized = normalizeClass2(value[i]);
        if (normalized) {
          res += normalized + " ";
        }
      }
    } else if (isObject2(value)) {
      for (const name in value) {
        if (value[name]) {
          res += name + " ";
        }
      }
    }
    return res.trim();
  }
  var specialBooleanAttrs2 = `itemscope,allowfullscreen,formnovalidate,ismap,nomodule,novalidate,readonly`;
  var isBooleanAttr2 = /* @__PURE__ */ makeMap2(
    specialBooleanAttrs2 + `,async,autofocus,autoplay,controls,default,defer,disabled,hidden,inert,loop,open,required,reversed,scoped,seamless,checked,muted,multiple,selected`
  );
  var toDisplayString2 = (val) => {
    return isString2(val) ? val : val == null ? "" : isArray2(val) || isObject2(val) && (val.toString === objectToString2 || !isFunction2(val.toString)) ? JSON.stringify(val, replacer2, 2) : String(val);
  };
  var replacer2 = (_key, val) => {
    if (val && val.__v_isRef) {
      return replacer2(_key, val.value);
    } else if (isMap2(val)) {
      return {
        [`Map(${val.size})`]: [...val.entries()].reduce((entries, [key, val2]) => {
          entries[`${key} =>`] = val2;
          return entries;
        }, {})
      };
    } else if (isSet2(val)) {
      return {
        [`Set(${val.size})`]: [...val.values()]
      };
    } else if (isObject2(val) && !isArray2(val) && !isPlainObject2(val)) {
      return String(val);
    }
    return val;
  };

  // node_modules/@vue/reactivity/dist/reactivity.esm-bundler.js
  function warn3(msg, ...args) {
    console.warn(`[Vue warn] ${msg}`, ...args);
  }
  var activeEffectScope2;
  function recordEffectScope(effect6, scope = activeEffectScope2) {
    if (scope && scope.active) {
      scope.effects.push(effect6);
    }
  }
  function getCurrentScope2() {
    return activeEffectScope2;
  }
  var createDep = (effects) => {
    const dep = new Set(effects);
    dep.w = 0;
    dep.n = 0;
    return dep;
  };
  var wasTracked = (dep) => (dep.w & trackOpBit) > 0;
  var newTracked = (dep) => (dep.n & trackOpBit) > 0;
  var initDepMarkers = ({ deps }) => {
    if (deps.length) {
      for (let i = 0; i < deps.length; i++) {
        deps[i].w |= trackOpBit;
      }
    }
  };
  var finalizeDepMarkers = (effect6) => {
    const { deps } = effect6;
    if (deps.length) {
      let ptr = 0;
      for (let i = 0; i < deps.length; i++) {
        const dep = deps[i];
        if (wasTracked(dep) && !newTracked(dep)) {
          dep.delete(effect6);
        } else {
          deps[ptr++] = dep;
        }
        dep.w &= ~trackOpBit;
        dep.n &= ~trackOpBit;
      }
      deps.length = ptr;
    }
  };
  var targetMap2 = /* @__PURE__ */ new WeakMap();
  var effectTrackDepth = 0;
  var trackOpBit = 1;
  var maxMarkerBits = 30;
  var activeEffect;
  var ITERATE_KEY2 = Symbol(true ? "iterate" : "");
  var MAP_KEY_ITERATE_KEY2 = Symbol(true ? "Map key iterate" : "");
  var ReactiveEffect2 = class {
    constructor(fn2, scheduler = null, scope) {
      this.fn = fn2;
      this.scheduler = scheduler;
      this.active = true;
      this.deps = [];
      this.parent = void 0;
      recordEffectScope(this, scope);
    }
    run() {
      if (!this.active) {
        return this.fn();
      }
      let parent = activeEffect;
      let lastShouldTrack = shouldTrack2;
      while (parent) {
        if (parent === this) {
          return;
        }
        parent = parent.parent;
      }
      try {
        this.parent = activeEffect;
        activeEffect = this;
        shouldTrack2 = true;
        trackOpBit = 1 << ++effectTrackDepth;
        if (effectTrackDepth <= maxMarkerBits) {
          initDepMarkers(this);
        } else {
          cleanupEffect2(this);
        }
        return this.fn();
      } finally {
        if (effectTrackDepth <= maxMarkerBits) {
          finalizeDepMarkers(this);
        }
        trackOpBit = 1 << --effectTrackDepth;
        activeEffect = this.parent;
        shouldTrack2 = lastShouldTrack;
        this.parent = void 0;
        if (this.deferStop) {
          this.stop();
        }
      }
    }
    stop() {
      if (activeEffect === this) {
        this.deferStop = true;
      } else if (this.active) {
        cleanupEffect2(this);
        if (this.onStop) {
          this.onStop();
        }
        this.active = false;
      }
    }
  };
  function cleanupEffect2(effect22) {
    const { deps } = effect22;
    if (deps.length) {
      for (let i = 0; i < deps.length; i++) {
        deps[i].delete(effect22);
      }
      deps.length = 0;
    }
  }
  var shouldTrack2 = true;
  var trackStack2 = [];
  function pauseTracking2() {
    trackStack2.push(shouldTrack2);
    shouldTrack2 = false;
  }
  function resetTracking2() {
    const last = trackStack2.pop();
    shouldTrack2 = last === void 0 ? true : last;
  }
  function track2(target, type, key) {
    if (shouldTrack2 && activeEffect) {
      let depsMap = targetMap2.get(target);
      if (!depsMap) {
        targetMap2.set(target, depsMap = /* @__PURE__ */ new Map());
      }
      let dep = depsMap.get(key);
      if (!dep) {
        depsMap.set(key, dep = createDep());
      }
      const eventInfo = true ? { effect: activeEffect, target, type, key } : void 0;
      trackEffects(dep, eventInfo);
    }
  }
  function trackEffects(dep, debuggerEventExtraInfo) {
    let shouldTrack22 = false;
    if (effectTrackDepth <= maxMarkerBits) {
      if (!newTracked(dep)) {
        dep.n |= trackOpBit;
        shouldTrack22 = !wasTracked(dep);
      }
    } else {
      shouldTrack22 = !dep.has(activeEffect);
    }
    if (shouldTrack22) {
      dep.add(activeEffect);
      activeEffect.deps.push(dep);
      if (activeEffect.onTrack) {
        activeEffect.onTrack(
          extend2(
            {
              effect: activeEffect
            },
            debuggerEventExtraInfo
          )
        );
      }
    }
  }
  function trigger2(target, type, key, newValue, oldValue, oldTarget) {
    const depsMap = targetMap2.get(target);
    if (!depsMap) {
      return;
    }
    let deps = [];
    if (type === "clear") {
      deps = [...depsMap.values()];
    } else if (key === "length" && isArray2(target)) {
      const newLength = Number(newValue);
      depsMap.forEach((dep, key2) => {
        if (key2 === "length" || !isSymbol2(key2) && key2 >= newLength) {
          deps.push(dep);
        }
      });
    } else {
      if (key !== void 0) {
        deps.push(depsMap.get(key));
      }
      switch (type) {
        case "add":
          if (!isArray2(target)) {
            deps.push(depsMap.get(ITERATE_KEY2));
            if (isMap2(target)) {
              deps.push(depsMap.get(MAP_KEY_ITERATE_KEY2));
            }
          } else if (isIntegerKey2(key)) {
            deps.push(depsMap.get("length"));
          }
          break;
        case "delete":
          if (!isArray2(target)) {
            deps.push(depsMap.get(ITERATE_KEY2));
            if (isMap2(target)) {
              deps.push(depsMap.get(MAP_KEY_ITERATE_KEY2));
            }
          }
          break;
        case "set":
          if (isMap2(target)) {
            deps.push(depsMap.get(ITERATE_KEY2));
          }
          break;
      }
    }
    const eventInfo = true ? { target, type, key, newValue, oldValue, oldTarget } : void 0;
    if (deps.length === 1) {
      if (deps[0]) {
        if (true) {
          triggerEffects(deps[0], eventInfo);
        } else {
          triggerEffects(deps[0]);
        }
      }
    } else {
      const effects = [];
      for (const dep of deps) {
        if (dep) {
          effects.push(...dep);
        }
      }
      if (true) {
        triggerEffects(createDep(effects), eventInfo);
      } else {
        triggerEffects(createDep(effects));
      }
    }
  }
  function triggerEffects(dep, debuggerEventExtraInfo) {
    const effects = isArray2(dep) ? dep : [...dep];
    for (const effect22 of effects) {
      if (effect22.computed) {
        triggerEffect(effect22, debuggerEventExtraInfo);
      }
    }
    for (const effect22 of effects) {
      if (!effect22.computed) {
        triggerEffect(effect22, debuggerEventExtraInfo);
      }
    }
  }
  function triggerEffect(effect22, debuggerEventExtraInfo) {
    if (effect22 !== activeEffect || effect22.allowRecurse) {
      if (effect22.onTrigger) {
        effect22.onTrigger(extend2({ effect: effect22 }, debuggerEventExtraInfo));
      }
      if (effect22.scheduler) {
        effect22.scheduler();
      } else {
        effect22.run();
      }
    }
  }
  var isNonTrackableKeys2 = /* @__PURE__ */ makeMap2(`__proto__,__v_isRef,__isVue`);
  var builtInSymbols2 = new Set(
    /* @__PURE__ */ Object.getOwnPropertyNames(Symbol).filter((key) => key !== "arguments" && key !== "caller").map((key) => Symbol[key]).filter(isSymbol2)
  );
  var arrayInstrumentations2 = /* @__PURE__ */ createArrayInstrumentations();
  function createArrayInstrumentations() {
    const instrumentations = {};
    ["includes", "indexOf", "lastIndexOf"].forEach((key) => {
      instrumentations[key] = function(...args) {
        const arr = toRaw2(this);
        for (let i = 0, l = this.length; i < l; i++) {
          track2(arr, "get", i + "");
        }
        const res = arr[key](...args);
        if (res === -1 || res === false) {
          return arr[key](...args.map(toRaw2));
        } else {
          return res;
        }
      };
    });
    ["push", "pop", "shift", "unshift", "splice"].forEach((key) => {
      instrumentations[key] = function(...args) {
        pauseTracking2();
        const res = toRaw2(this)[key].apply(this, args);
        resetTracking2();
        return res;
      };
    });
    return instrumentations;
  }
  function hasOwnProperty4(key) {
    const obj = toRaw2(this);
    track2(obj, "has", key);
    return obj.hasOwnProperty(key);
  }
  var BaseReactiveHandler2 = class {
    constructor(_isReadonly = false, _shallow = false) {
      this._isReadonly = _isReadonly;
      this._shallow = _shallow;
    }
    get(target, key, receiver) {
      const isReadonly22 = this._isReadonly, shallow = this._shallow;
      if (key === "__v_isReactive") {
        return !isReadonly22;
      } else if (key === "__v_isReadonly") {
        return isReadonly22;
      } else if (key === "__v_isShallow") {
        return shallow;
      } else if (key === "__v_raw" && receiver === (isReadonly22 ? shallow ? shallowReadonlyMap2 : readonlyMap2 : shallow ? shallowReactiveMap2 : reactiveMap2).get(target)) {
        return target;
      }
      const targetIsArray = isArray2(target);
      if (!isReadonly22) {
        if (targetIsArray && hasOwn2(arrayInstrumentations2, key)) {
          return Reflect.get(arrayInstrumentations2, key, receiver);
        }
        if (key === "hasOwnProperty") {
          return hasOwnProperty4;
        }
      }
      const res = Reflect.get(target, key, receiver);
      if (isSymbol2(key) ? builtInSymbols2.has(key) : isNonTrackableKeys2(key)) {
        return res;
      }
      if (!isReadonly22) {
        track2(target, "get", key);
      }
      if (shallow) {
        return res;
      }
      if (isRef3(res)) {
        return targetIsArray && isIntegerKey2(key) ? res : res.value;
      }
      if (isObject2(res)) {
        return isReadonly22 ? readonly2(res) : reactive2(res);
      }
      return res;
    }
  };
  var MutableReactiveHandler2 = class extends BaseReactiveHandler2 {
    constructor(shallow = false) {
      super(false, shallow);
    }
    set(target, key, value, receiver) {
      let oldValue = target[key];
      if (isReadonly2(oldValue) && isRef3(oldValue) && !isRef3(value)) {
        return false;
      }
      if (!this._shallow) {
        if (!isShallow2(value) && !isReadonly2(value)) {
          oldValue = toRaw2(oldValue);
          value = toRaw2(value);
        }
        if (!isArray2(target) && isRef3(oldValue) && !isRef3(value)) {
          oldValue.value = value;
          return true;
        }
      }
      const hadKey = isArray2(target) && isIntegerKey2(key) ? Number(key) < target.length : hasOwn2(target, key);
      const result = Reflect.set(target, key, value, receiver);
      if (target === toRaw2(receiver)) {
        if (!hadKey) {
          trigger2(target, "add", key, value);
        } else if (hasChanged2(value, oldValue)) {
          trigger2(target, "set", key, value, oldValue);
        }
      }
      return result;
    }
    deleteProperty(target, key) {
      const hadKey = hasOwn2(target, key);
      const oldValue = target[key];
      const result = Reflect.deleteProperty(target, key);
      if (result && hadKey) {
        trigger2(target, "delete", key, void 0, oldValue);
      }
      return result;
    }
    has(target, key) {
      const result = Reflect.has(target, key);
      if (!isSymbol2(key) || !builtInSymbols2.has(key)) {
        track2(target, "has", key);
      }
      return result;
    }
    ownKeys(target) {
      track2(
        target,
        "iterate",
        isArray2(target) ? "length" : ITERATE_KEY2
      );
      return Reflect.ownKeys(target);
    }
  };
  var ReadonlyReactiveHandler2 = class extends BaseReactiveHandler2 {
    constructor(shallow = false) {
      super(true, shallow);
    }
    set(target, key) {
      if (true) {
        warn3(
          `Set operation on key "${String(key)}" failed: target is readonly.`,
          target
        );
      }
      return true;
    }
    deleteProperty(target, key) {
      if (true) {
        warn3(
          `Delete operation on key "${String(key)}" failed: target is readonly.`,
          target
        );
      }
      return true;
    }
  };
  var mutableHandlers2 = /* @__PURE__ */ new MutableReactiveHandler2();
  var readonlyHandlers2 = /* @__PURE__ */ new ReadonlyReactiveHandler2();
  var shallowReadonlyHandlers2 = /* @__PURE__ */ new ReadonlyReactiveHandler2(true);
  var toShallow2 = (value) => value;
  var getProto2 = (v) => Reflect.getPrototypeOf(v);
  function get(target, key, isReadonly3 = false, isShallow4 = false) {
    target = target["__v_raw"];
    const rawTarget = toRaw2(target);
    const rawKey = toRaw2(key);
    if (!isReadonly3) {
      if (hasChanged2(key, rawKey)) {
        track2(rawTarget, "get", key);
      }
      track2(rawTarget, "get", rawKey);
    }
    const { has: has2 } = getProto2(rawTarget);
    const wrap = isShallow4 ? toShallow2 : isReadonly3 ? toReadonly2 : toReactive2;
    if (has2.call(rawTarget, key)) {
      return wrap(target.get(key));
    } else if (has2.call(rawTarget, rawKey)) {
      return wrap(target.get(rawKey));
    } else if (target !== rawTarget) {
      target.get(key);
    }
  }
  function has(key, isReadonly3 = false) {
    const target = this["__v_raw"];
    const rawTarget = toRaw2(target);
    const rawKey = toRaw2(key);
    if (!isReadonly3) {
      if (hasChanged2(key, rawKey)) {
        track2(rawTarget, "has", key);
      }
      track2(rawTarget, "has", rawKey);
    }
    return key === rawKey ? target.has(key) : target.has(key) || target.has(rawKey);
  }
  function size(target, isReadonly3 = false) {
    target = target["__v_raw"];
    !isReadonly3 && track2(toRaw2(target), "iterate", ITERATE_KEY2);
    return Reflect.get(target, "size", target);
  }
  function add(value) {
    value = toRaw2(value);
    const target = toRaw2(this);
    const proto = getProto2(target);
    const hadKey = proto.has.call(target, value);
    if (!hadKey) {
      target.add(value);
      trigger2(target, "add", value, value);
    }
    return this;
  }
  function set(key, value) {
    value = toRaw2(value);
    const target = toRaw2(this);
    const { has: has2, get: get2 } = getProto2(target);
    let hadKey = has2.call(target, key);
    if (!hadKey) {
      key = toRaw2(key);
      hadKey = has2.call(target, key);
    } else if (true) {
      checkIdentityKeys2(target, has2, key);
    }
    const oldValue = get2.call(target, key);
    target.set(key, value);
    if (!hadKey) {
      trigger2(target, "add", key, value);
    } else if (hasChanged2(value, oldValue)) {
      trigger2(target, "set", key, value, oldValue);
    }
    return this;
  }
  function deleteEntry(key) {
    const target = toRaw2(this);
    const { has: has2, get: get2 } = getProto2(target);
    let hadKey = has2.call(target, key);
    if (!hadKey) {
      key = toRaw2(key);
      hadKey = has2.call(target, key);
    } else if (true) {
      checkIdentityKeys2(target, has2, key);
    }
    const oldValue = get2 ? get2.call(target, key) : void 0;
    const result = target.delete(key);
    if (hadKey) {
      trigger2(target, "delete", key, void 0, oldValue);
    }
    return result;
  }
  function clear() {
    const target = toRaw2(this);
    const hadItems = target.size !== 0;
    const oldTarget = true ? isMap2(target) ? new Map(target) : new Set(target) : void 0;
    const result = target.clear();
    if (hadItems) {
      trigger2(target, "clear", void 0, void 0, oldTarget);
    }
    return result;
  }
  function createForEach(isReadonly3, isShallow4) {
    return function forEach(callback, thisArg) {
      const observed = this;
      const target = observed["__v_raw"];
      const rawTarget = toRaw2(target);
      const wrap = isShallow4 ? toShallow2 : isReadonly3 ? toReadonly2 : toReactive2;
      !isReadonly3 && track2(rawTarget, "iterate", ITERATE_KEY2);
      return target.forEach((value, key) => {
        return callback.call(thisArg, wrap(value), wrap(key), observed);
      });
    };
  }
  function createIterableMethod2(method, isReadonly3, isShallow4) {
    return function(...args) {
      const target = this["__v_raw"];
      const rawTarget = toRaw2(target);
      const targetIsMap = isMap2(rawTarget);
      const isPair = method === "entries" || method === Symbol.iterator && targetIsMap;
      const isKeyOnly = method === "keys" && targetIsMap;
      const innerIterator = target[method](...args);
      const wrap = isShallow4 ? toShallow2 : isReadonly3 ? toReadonly2 : toReactive2;
      !isReadonly3 && track2(
        rawTarget,
        "iterate",
        isKeyOnly ? MAP_KEY_ITERATE_KEY2 : ITERATE_KEY2
      );
      return {
        next() {
          const { value, done } = innerIterator.next();
          return done ? { value, done } : {
            value: isPair ? [wrap(value[0]), wrap(value[1])] : wrap(value),
            done
          };
        },
        [Symbol.iterator]() {
          return this;
        }
      };
    };
  }
  function createReadonlyMethod2(type) {
    return function(...args) {
      if (true) {
        const key = args[0] ? `on key "${args[0]}" ` : ``;
        console.warn(
          `${capitalize2(type)} operation ${key}failed: target is readonly.`,
          toRaw2(this)
        );
      }
      return type === "delete" ? false : type === "clear" ? void 0 : this;
    };
  }
  function createInstrumentations2() {
    const mutableInstrumentations2 = {
      get(key) {
        return get(this, key);
      },
      get size() {
        return size(this);
      },
      has,
      add,
      set,
      delete: deleteEntry,
      clear,
      forEach: createForEach(false, false)
    };
    const shallowInstrumentations2 = {
      get(key) {
        return get(this, key, false, true);
      },
      get size() {
        return size(this);
      },
      has,
      add,
      set,
      delete: deleteEntry,
      clear,
      forEach: createForEach(false, true)
    };
    const readonlyInstrumentations2 = {
      get(key) {
        return get(this, key, true);
      },
      get size() {
        return size(this, true);
      },
      has(key) {
        return has.call(this, key, true);
      },
      add: createReadonlyMethod2("add"),
      set: createReadonlyMethod2("set"),
      delete: createReadonlyMethod2("delete"),
      clear: createReadonlyMethod2("clear"),
      forEach: createForEach(true, false)
    };
    const shallowReadonlyInstrumentations2 = {
      get(key) {
        return get(this, key, true, true);
      },
      get size() {
        return size(this, true);
      },
      has(key) {
        return has.call(this, key, true);
      },
      add: createReadonlyMethod2("add"),
      set: createReadonlyMethod2("set"),
      delete: createReadonlyMethod2("delete"),
      clear: createReadonlyMethod2("clear"),
      forEach: createForEach(true, true)
    };
    const iteratorMethods = ["keys", "values", "entries", Symbol.iterator];
    iteratorMethods.forEach((method) => {
      mutableInstrumentations2[method] = createIterableMethod2(
        method,
        false,
        false
      );
      readonlyInstrumentations2[method] = createIterableMethod2(
        method,
        true,
        false
      );
      shallowInstrumentations2[method] = createIterableMethod2(
        method,
        false,
        true
      );
      shallowReadonlyInstrumentations2[method] = createIterableMethod2(
        method,
        true,
        true
      );
    });
    return [
      mutableInstrumentations2,
      readonlyInstrumentations2,
      shallowInstrumentations2,
      shallowReadonlyInstrumentations2
    ];
  }
  var [
    mutableInstrumentations,
    readonlyInstrumentations,
    shallowInstrumentations,
    shallowReadonlyInstrumentations
  ] = /* @__PURE__ */ createInstrumentations2();
  function createInstrumentationGetter2(isReadonly3, shallow) {
    const instrumentations = shallow ? isReadonly3 ? shallowReadonlyInstrumentations : shallowInstrumentations : isReadonly3 ? readonlyInstrumentations : mutableInstrumentations;
    return (target, key, receiver) => {
      if (key === "__v_isReactive") {
        return !isReadonly3;
      } else if (key === "__v_isReadonly") {
        return isReadonly3;
      } else if (key === "__v_raw") {
        return target;
      }
      return Reflect.get(
        hasOwn2(instrumentations, key) && key in target ? instrumentations : target,
        key,
        receiver
      );
    };
  }
  var mutableCollectionHandlers2 = {
    get: /* @__PURE__ */ createInstrumentationGetter2(false, false)
  };
  var readonlyCollectionHandlers2 = {
    get: /* @__PURE__ */ createInstrumentationGetter2(true, false)
  };
  var shallowReadonlyCollectionHandlers2 = {
    get: /* @__PURE__ */ createInstrumentationGetter2(true, true)
  };
  function checkIdentityKeys2(target, has2, key) {
    const rawKey = toRaw2(key);
    if (rawKey !== key && has2.call(target, rawKey)) {
      const type = toRawType2(target);
      console.warn(
        `Reactive ${type} contains both the raw and reactive versions of the same object${type === `Map` ? ` as keys` : ``}, which can lead to inconsistencies. Avoid differentiating between the raw and reactive versions of an object and only use the reactive version if possible.`
      );
    }
  }
  var reactiveMap2 = /* @__PURE__ */ new WeakMap();
  var shallowReactiveMap2 = /* @__PURE__ */ new WeakMap();
  var readonlyMap2 = /* @__PURE__ */ new WeakMap();
  var shallowReadonlyMap2 = /* @__PURE__ */ new WeakMap();
  function targetTypeMap2(rawType) {
    switch (rawType) {
      case "Object":
      case "Array":
        return 1;
      case "Map":
      case "Set":
      case "WeakMap":
      case "WeakSet":
        return 2;
      default:
        return 0;
    }
  }
  function getTargetType2(value) {
    return value["__v_skip"] || !Object.isExtensible(value) ? 0 : targetTypeMap2(toRawType2(value));
  }
  function reactive2(target) {
    if (isReadonly2(target)) {
      return target;
    }
    return createReactiveObject2(
      target,
      false,
      mutableHandlers2,
      mutableCollectionHandlers2,
      reactiveMap2
    );
  }
  function readonly2(target) {
    return createReactiveObject2(
      target,
      true,
      readonlyHandlers2,
      readonlyCollectionHandlers2,
      readonlyMap2
    );
  }
  function shallowReadonly2(target) {
    return createReactiveObject2(
      target,
      true,
      shallowReadonlyHandlers2,
      shallowReadonlyCollectionHandlers2,
      shallowReadonlyMap2
    );
  }
  function createReactiveObject2(target, isReadonly22, baseHandlers, collectionHandlers, proxyMap) {
    if (!isObject2(target)) {
      if (true) {
        console.warn(`value cannot be made reactive: ${String(target)}`);
      }
      return target;
    }
    if (target["__v_raw"] && !(isReadonly22 && target["__v_isReactive"])) {
      return target;
    }
    const existingProxy = proxyMap.get(target);
    if (existingProxy) {
      return existingProxy;
    }
    const targetType = getTargetType2(target);
    if (targetType === 0) {
      return target;
    }
    const proxy = new Proxy(
      target,
      targetType === 2 ? collectionHandlers : baseHandlers
    );
    proxyMap.set(target, proxy);
    return proxy;
  }
  function isReactive2(value) {
    if (isReadonly2(value)) {
      return isReactive2(value["__v_raw"]);
    }
    return !!(value && value["__v_isReactive"]);
  }
  function isReadonly2(value) {
    return !!(value && value["__v_isReadonly"]);
  }
  function isShallow2(value) {
    return !!(value && value["__v_isShallow"]);
  }
  function isProxy2(value) {
    return isReactive2(value) || isReadonly2(value);
  }
  function toRaw2(observed) {
    const raw = observed && observed["__v_raw"];
    return raw ? toRaw2(raw) : observed;
  }
  function markRaw2(value) {
    def2(value, "__v_skip", true);
    return value;
  }
  var toReactive2 = (value) => isObject2(value) ? reactive2(value) : value;
  var toReadonly2 = (value) => isObject2(value) ? readonly2(value) : value;
  function trackRefValue(ref22) {
    if (shouldTrack2 && activeEffect) {
      ref22 = toRaw2(ref22);
      if (true) {
        trackEffects(ref22.dep || (ref22.dep = createDep()), {
          target: ref22,
          type: "get",
          key: "value"
        });
      } else {
        trackEffects(ref22.dep || (ref22.dep = createDep()));
      }
    }
  }
  function triggerRefValue(ref22, newVal) {
    ref22 = toRaw2(ref22);
    const dep = ref22.dep;
    if (dep) {
      if (true) {
        triggerEffects(dep, {
          target: ref22,
          type: "set",
          key: "value",
          newValue: newVal
        });
      } else {
        triggerEffects(dep);
      }
    }
  }
  function isRef3(r) {
    return !!(r && r.__v_isRef === true);
  }
  function ref2(value) {
    return createRef2(value, false);
  }
  function createRef2(rawValue, shallow) {
    if (isRef3(rawValue)) {
      return rawValue;
    }
    return new RefImpl2(rawValue, shallow);
  }
  var RefImpl2 = class {
    constructor(value, __v_isShallow) {
      this.__v_isShallow = __v_isShallow;
      this.dep = void 0;
      this.__v_isRef = true;
      this._rawValue = __v_isShallow ? value : toRaw2(value);
      this._value = __v_isShallow ? value : toReactive2(value);
    }
    get value() {
      trackRefValue(this);
      return this._value;
    }
    set value(newVal) {
      const useDirectValue = this.__v_isShallow || isShallow2(newVal) || isReadonly2(newVal);
      newVal = useDirectValue ? newVal : toRaw2(newVal);
      if (hasChanged2(newVal, this._rawValue)) {
        this._rawValue = newVal;
        this._value = useDirectValue ? newVal : toReactive2(newVal);
        triggerRefValue(this, newVal);
      }
    }
  };
  function unref2(ref22) {
    return isRef3(ref22) ? ref22.value : ref22;
  }
  var shallowUnwrapHandlers2 = {
    get: (target, key, receiver) => unref2(Reflect.get(target, key, receiver)),
    set: (target, key, value, receiver) => {
      const oldValue = target[key];
      if (isRef3(oldValue) && !isRef3(value)) {
        oldValue.value = value;
        return true;
      } else {
        return Reflect.set(target, key, value, receiver);
      }
    }
  };
  function proxyRefs2(objectWithRefs) {
    return isReactive2(objectWithRefs) ? objectWithRefs : new Proxy(objectWithRefs, shallowUnwrapHandlers2);
  }
  var ComputedRefImpl2 = class {
    constructor(getter, _setter, isReadonly3, isSSR) {
      this._setter = _setter;
      this.dep = void 0;
      this.__v_isRef = true;
      this["__v_isReadonly"] = false;
      this._dirty = true;
      this.effect = new ReactiveEffect2(getter, () => {
        if (!this._dirty) {
          this._dirty = true;
          triggerRefValue(this);
        }
      });
      this.effect.computed = this;
      this.effect.active = this._cacheable = !isSSR;
      this["__v_isReadonly"] = isReadonly3;
    }
    get value() {
      const self2 = toRaw2(this);
      trackRefValue(self2);
      if (self2._dirty || !self2._cacheable) {
        self2._dirty = false;
        self2._value = self2.effect.run();
      }
      return self2._value;
    }
    set value(newValue) {
      this._setter(newValue);
    }
  };
  function computed3(getterOrOptions, debugOptions, isSSR = false) {
    let getter;
    let setter;
    const onlyGetter = isFunction2(getterOrOptions);
    if (onlyGetter) {
      getter = getterOrOptions;
      setter = true ? () => {
        console.warn("Write operation failed: computed value is readonly");
      } : NOOP2;
    } else {
      getter = getterOrOptions.get;
      setter = getterOrOptions.set;
    }
    const cRef = new ComputedRefImpl2(getter, setter, onlyGetter || !setter, isSSR);
    if (debugOptions && !isSSR) {
      cRef.effect.onTrack = debugOptions.onTrack;
      cRef.effect.onTrigger = debugOptions.onTrigger;
    }
    return cRef;
  }

  // node_modules/@vue/runtime-core/dist/runtime-core.esm-bundler.js
  var stack2 = [];
  function pushWarningContext2(vnode) {
    stack2.push(vnode);
  }
  function popWarningContext2() {
    stack2.pop();
  }
  function warn4(msg, ...args) {
    if (false)
      return;
    pauseTracking2();
    const instance = stack2.length ? stack2[stack2.length - 1].component : null;
    const appWarnHandler = instance && instance.appContext.config.warnHandler;
    const trace = getComponentTrace2();
    if (appWarnHandler) {
      callWithErrorHandling2(
        appWarnHandler,
        instance,
        11,
        [
          msg + args.join(""),
          instance && instance.proxy,
          trace.map(
            ({ vnode }) => `at <${formatComponentName2(instance, vnode.type)}>`
          ).join("\n"),
          trace
        ]
      );
    } else {
      const warnArgs = [`[Vue warn]: ${msg}`, ...args];
      if (trace.length && true) {
        warnArgs.push(`
`, ...formatTrace2(trace));
      }
      console.warn(...warnArgs);
    }
    resetTracking2();
  }
  function getComponentTrace2() {
    let currentVNode = stack2[stack2.length - 1];
    if (!currentVNode) {
      return [];
    }
    const normalizedStack = [];
    while (currentVNode) {
      const last = normalizedStack[0];
      if (last && last.vnode === currentVNode) {
        last.recurseCount++;
      } else {
        normalizedStack.push({
          vnode: currentVNode,
          recurseCount: 0
        });
      }
      const parentInstance = currentVNode.component && currentVNode.component.parent;
      currentVNode = parentInstance && parentInstance.vnode;
    }
    return normalizedStack;
  }
  function formatTrace2(trace) {
    const logs = [];
    trace.forEach((entry, i) => {
      logs.push(...i === 0 ? [] : [`
`], ...formatTraceEntry2(entry));
    });
    return logs;
  }
  function formatTraceEntry2({ vnode, recurseCount }) {
    const postfix = recurseCount > 0 ? `... (${recurseCount} recursive calls)` : ``;
    const isRoot = vnode.component ? vnode.component.parent == null : false;
    const open = ` at <${formatComponentName2(
      vnode.component,
      vnode.type,
      isRoot
    )}`;
    const close = `>` + postfix;
    return vnode.props ? [open, ...formatProps2(vnode.props), close] : [open + close];
  }
  function formatProps2(props) {
    const res = [];
    const keys = Object.keys(props);
    keys.slice(0, 3).forEach((key) => {
      res.push(...formatProp2(key, props[key]));
    });
    if (keys.length > 3) {
      res.push(` ...`);
    }
    return res;
  }
  function formatProp2(key, value, raw) {
    if (isString2(value)) {
      value = JSON.stringify(value);
      return raw ? value : [`${key}=${value}`];
    } else if (typeof value === "number" || typeof value === "boolean" || value == null) {
      return raw ? value : [`${key}=${value}`];
    } else if (isRef3(value)) {
      value = formatProp2(key, toRaw2(value.value), true);
      return raw ? value : [`${key}=Ref<`, value, `>`];
    } else if (isFunction2(value)) {
      return [`${key}=fn${value.name ? `<${value.name}>` : ``}`];
    } else {
      value = toRaw2(value);
      return raw ? value : [`${key}=`, value];
    }
  }
  function assertNumber2(val, type) {
    if (false)
      return;
    if (val === void 0) {
      return;
    } else if (typeof val !== "number") {
      warn4(`${type} is not a valid number - got ${JSON.stringify(val)}.`);
    } else if (isNaN(val)) {
      warn4(`${type} is NaN - the duration expression might be incorrect.`);
    }
  }
  var ErrorTypeStrings = {
    ["sp"]: "serverPrefetch hook",
    ["bc"]: "beforeCreate hook",
    ["c"]: "created hook",
    ["bm"]: "beforeMount hook",
    ["m"]: "mounted hook",
    ["bu"]: "beforeUpdate hook",
    ["u"]: "updated",
    ["bum"]: "beforeUnmount hook",
    ["um"]: "unmounted hook",
    ["a"]: "activated hook",
    ["da"]: "deactivated hook",
    ["ec"]: "errorCaptured hook",
    ["rtc"]: "renderTracked hook",
    ["rtg"]: "renderTriggered hook",
    [0]: "setup function",
    [1]: "render function",
    [2]: "watcher getter",
    [3]: "watcher callback",
    [4]: "watcher cleanup function",
    [5]: "native event handler",
    [6]: "component event handler",
    [7]: "vnode hook",
    [8]: "directive hook",
    [9]: "transition hook",
    [10]: "app errorHandler",
    [11]: "app warnHandler",
    [12]: "ref function",
    [13]: "async component loader",
    [14]: "scheduler flush. This is likely a Vue internals bug. Please open an issue at https://new-issue.vuejs.org/?repo=vuejs/core"
  };
  function callWithErrorHandling2(fn2, instance, type, args) {
    let res;
    try {
      res = args ? fn2(...args) : fn2();
    } catch (err) {
      handleError2(err, instance, type);
    }
    return res;
  }
  function callWithAsyncErrorHandling2(fn2, instance, type, args) {
    if (isFunction2(fn2)) {
      const res = callWithErrorHandling2(fn2, instance, type, args);
      if (res && isPromise2(res)) {
        res.catch((err) => {
          handleError2(err, instance, type);
        });
      }
      return res;
    }
    const values = [];
    for (let i = 0; i < fn2.length; i++) {
      values.push(callWithAsyncErrorHandling2(fn2[i], instance, type, args));
    }
    return values;
  }
  function handleError2(err, instance, type, throwInDev = true) {
    const contextVNode = instance ? instance.vnode : null;
    if (instance) {
      let cur = instance.parent;
      const exposedInstance = instance.proxy;
      const errorInfo = true ? ErrorTypeStrings[type] : type;
      while (cur) {
        const errorCapturedHooks = cur.ec;
        if (errorCapturedHooks) {
          for (let i = 0; i < errorCapturedHooks.length; i++) {
            if (errorCapturedHooks[i](err, exposedInstance, errorInfo) === false) {
              return;
            }
          }
        }
        cur = cur.parent;
      }
      const appErrorHandler = instance.appContext.config.errorHandler;
      if (appErrorHandler) {
        callWithErrorHandling2(
          appErrorHandler,
          null,
          10,
          [err, exposedInstance, errorInfo]
        );
        return;
      }
    }
    logError2(err, type, contextVNode, throwInDev);
  }
  function logError2(err, type, contextVNode, throwInDev = true) {
    if (true) {
      const info = ErrorTypeStrings[type];
      if (contextVNode) {
        pushWarningContext2(contextVNode);
      }
      warn4(`Unhandled error${info ? ` during execution of ${info}` : ``}`);
      if (contextVNode) {
        popWarningContext2();
      }
      if (throwInDev) {
        throw err;
      } else {
        console.error(err);
      }
    } else {
      console.error(err);
    }
  }
  var isFlushing = false;
  var isFlushPending = false;
  var queue2 = [];
  var flushIndex2 = 0;
  var pendingPostFlushCbs2 = [];
  var activePostFlushCbs2 = null;
  var postFlushIndex2 = 0;
  var resolvedPromise2 = /* @__PURE__ */ Promise.resolve();
  var currentFlushPromise2 = null;
  var RECURSION_LIMIT2 = 100;
  function nextTick2(fn2) {
    const p2 = currentFlushPromise2 || resolvedPromise2;
    return fn2 ? p2.then(this ? fn2.bind(this) : fn2) : p2;
  }
  function findInsertionIndex2(id) {
    let start2 = flushIndex2 + 1;
    let end2 = queue2.length;
    while (start2 < end2) {
      const middle = start2 + end2 >>> 1;
      const middleJob = queue2[middle];
      const middleJobId = getId2(middleJob);
      if (middleJobId < id || middleJobId === id && middleJob.pre) {
        start2 = middle + 1;
      } else {
        end2 = middle;
      }
    }
    return start2;
  }
  function queueJob2(job) {
    if (!queue2.length || !queue2.includes(
      job,
      isFlushing && job.allowRecurse ? flushIndex2 + 1 : flushIndex2
    )) {
      if (job.id == null) {
        queue2.push(job);
      } else {
        queue2.splice(findInsertionIndex2(job.id), 0, job);
      }
      queueFlush2();
    }
  }
  function queueFlush2() {
    if (!isFlushing && !isFlushPending) {
      isFlushPending = true;
      currentFlushPromise2 = resolvedPromise2.then(flushJobs2);
    }
  }
  function queuePostFlushCb2(cb) {
    if (!isArray2(cb)) {
      if (!activePostFlushCbs2 || !activePostFlushCbs2.includes(
        cb,
        cb.allowRecurse ? postFlushIndex2 + 1 : postFlushIndex2
      )) {
        pendingPostFlushCbs2.push(cb);
      }
    } else {
      pendingPostFlushCbs2.push(...cb);
    }
    queueFlush2();
  }
  function flushPostFlushCbs2(seen) {
    if (pendingPostFlushCbs2.length) {
      const deduped = [...new Set(pendingPostFlushCbs2)];
      pendingPostFlushCbs2.length = 0;
      if (activePostFlushCbs2) {
        activePostFlushCbs2.push(...deduped);
        return;
      }
      activePostFlushCbs2 = deduped;
      if (true) {
        seen = seen || /* @__PURE__ */ new Map();
      }
      activePostFlushCbs2.sort((a, b) => getId2(a) - getId2(b));
      for (postFlushIndex2 = 0; postFlushIndex2 < activePostFlushCbs2.length; postFlushIndex2++) {
        if (checkRecursiveUpdates2(seen, activePostFlushCbs2[postFlushIndex2])) {
          continue;
        }
        activePostFlushCbs2[postFlushIndex2]();
      }
      activePostFlushCbs2 = null;
      postFlushIndex2 = 0;
    }
  }
  var getId2 = (job) => job.id == null ? Infinity : job.id;
  var comparator = (a, b) => {
    const diff = getId2(a) - getId2(b);
    if (diff === 0) {
      if (a.pre && !b.pre)
        return -1;
      if (b.pre && !a.pre)
        return 1;
    }
    return diff;
  };
  function flushJobs2(seen) {
    isFlushPending = false;
    isFlushing = true;
    if (true) {
      seen = seen || /* @__PURE__ */ new Map();
    }
    queue2.sort(comparator);
    const check = true ? (job) => checkRecursiveUpdates2(seen, job) : NOOP2;
    try {
      for (flushIndex2 = 0; flushIndex2 < queue2.length; flushIndex2++) {
        const job = queue2[flushIndex2];
        if (job && job.active !== false) {
          if (check(job)) {
            continue;
          }
          callWithErrorHandling2(job, null, 14);
        }
      }
    } finally {
      flushIndex2 = 0;
      queue2.length = 0;
      flushPostFlushCbs2(seen);
      isFlushing = false;
      currentFlushPromise2 = null;
      if (queue2.length || pendingPostFlushCbs2.length) {
        flushJobs2(seen);
      }
    }
  }
  function checkRecursiveUpdates2(seen, fn2) {
    if (!seen.has(fn2)) {
      seen.set(fn2, 1);
    } else {
      const count = seen.get(fn2);
      if (count > RECURSION_LIMIT2) {
        const instance = fn2.ownerInstance;
        const componentName = instance && getComponentName2(instance.type);
        warn4(
          `Maximum recursive updates exceeded${componentName ? ` in component <${componentName}>` : ``}. This means you have a reactive effect that is mutating its own dependencies and thus recursively triggering itself. Possible sources include component template, render function, updated hook or watcher source function.`
        );
        return true;
      } else {
        seen.set(fn2, count + 1);
      }
    }
  }
  var isHmrUpdating2 = false;
  var hmrDirtyComponents2 = /* @__PURE__ */ new Set();
  if (true) {
    getGlobalThis2().__VUE_HMR_RUNTIME__ = {
      createRecord: tryWrap2(createRecord2),
      rerender: tryWrap2(rerender2),
      reload: tryWrap2(reload2)
    };
  }
  var map2 = /* @__PURE__ */ new Map();
  function createRecord2(id, initialDef) {
    if (map2.has(id)) {
      return false;
    }
    map2.set(id, {
      initialDef: normalizeClassComponent2(initialDef),
      instances: /* @__PURE__ */ new Set()
    });
    return true;
  }
  function normalizeClassComponent2(component) {
    return isClassComponent2(component) ? component.__vccOpts : component;
  }
  function rerender2(id, newRender) {
    const record = map2.get(id);
    if (!record) {
      return;
    }
    record.initialDef.render = newRender;
    [...record.instances].forEach((instance) => {
      if (newRender) {
        instance.render = newRender;
        normalizeClassComponent2(instance.type).render = newRender;
      }
      instance.renderCache = [];
      isHmrUpdating2 = true;
      instance.update();
      isHmrUpdating2 = false;
    });
  }
  function reload2(id, newComp) {
    const record = map2.get(id);
    if (!record)
      return;
    newComp = normalizeClassComponent2(newComp);
    updateComponentDef2(record.initialDef, newComp);
    const instances = [...record.instances];
    for (const instance of instances) {
      const oldComp = normalizeClassComponent2(instance.type);
      if (!hmrDirtyComponents2.has(oldComp)) {
        if (oldComp !== record.initialDef) {
          updateComponentDef2(oldComp, newComp);
        }
        hmrDirtyComponents2.add(oldComp);
      }
      instance.appContext.propsCache.delete(instance.type);
      instance.appContext.emitsCache.delete(instance.type);
      instance.appContext.optionsCache.delete(instance.type);
      if (instance.ceReload) {
        hmrDirtyComponents2.add(oldComp);
        instance.ceReload(newComp.styles);
        hmrDirtyComponents2.delete(oldComp);
      } else if (instance.parent) {
        queueJob2(instance.parent.update);
      } else if (instance.appContext.reload) {
        instance.appContext.reload();
      } else if (typeof window !== "undefined") {
        window.location.reload();
      } else {
        console.warn(
          "[HMR] Root or manually mounted instance modified. Full reload required."
        );
      }
    }
    queuePostFlushCb2(() => {
      for (const instance of instances) {
        hmrDirtyComponents2.delete(
          normalizeClassComponent2(instance.type)
        );
      }
    });
  }
  function updateComponentDef2(oldComp, newComp) {
    extend2(oldComp, newComp);
    for (const key in oldComp) {
      if (key !== "__file" && !(key in newComp)) {
        delete oldComp[key];
      }
    }
  }
  function tryWrap2(fn2) {
    return (id, arg) => {
      try {
        return fn2(id, arg);
      } catch (e) {
        console.error(e);
        console.warn(
          `[HMR] Something went wrong during Vue component hot-reload. Full reload required.`
        );
      }
    };
  }
  var currentRenderingInstance2 = null;
  var currentScopeId2 = null;
  var accessedAttrs2 = false;
  function markAttrsAccessed2() {
    accessedAttrs2 = true;
  }
  var NULL_DYNAMIC_COMPONENT2 = Symbol.for("v-ndc");
  var isSuspense2 = (type) => type.__isSuspense;
  function queueEffectWithSuspense2(fn2, suspense) {
    if (suspense && suspense.pendingBranch) {
      if (isArray2(fn2)) {
        suspense.effects.push(...fn2);
      } else {
        suspense.effects.push(fn2);
      }
    } else {
      queuePostFlushCb2(fn2);
    }
  }
  var INITIAL_WATCHER_VALUE2 = {};
  function watch3(source, cb, options) {
    if (!isFunction2(cb)) {
      warn4(
        `\`watch(fn, options?)\` signature has been moved to a separate API. Use \`watchEffect(fn, options?)\` instead. \`watch\` now only supports \`watch(source, cb, options?) signature.`
      );
    }
    return doWatch2(source, cb, options);
  }
  function doWatch2(source, cb, { immediate, deep, flush, onTrack, onTrigger } = EMPTY_OBJ2) {
    var _a;
    if (!cb) {
      if (immediate !== void 0) {
        warn4(
          `watch() "immediate" option is only respected when using the watch(source, callback, options?) signature.`
        );
      }
      if (deep !== void 0) {
        warn4(
          `watch() "deep" option is only respected when using the watch(source, callback, options?) signature.`
        );
      }
    }
    const warnInvalidSource = (s) => {
      warn4(
        `Invalid watch source: `,
        s,
        `A watch source can only be a getter/effect function, a ref, a reactive object, or an array of these types.`
      );
    };
    const instance = getCurrentScope2() === ((_a = currentInstance2) == null ? void 0 : _a.scope) ? currentInstance2 : null;
    let getter;
    let forceTrigger = false;
    let isMultiSource = false;
    if (isRef3(source)) {
      getter = () => source.value;
      forceTrigger = isShallow2(source);
    } else if (isReactive2(source)) {
      getter = () => source;
      deep = true;
    } else if (isArray2(source)) {
      isMultiSource = true;
      forceTrigger = source.some((s) => isReactive2(s) || isShallow2(s));
      getter = () => source.map((s) => {
        if (isRef3(s)) {
          return s.value;
        } else if (isReactive2(s)) {
          return traverse2(s);
        } else if (isFunction2(s)) {
          return callWithErrorHandling2(s, instance, 2);
        } else {
          warnInvalidSource(s);
        }
      });
    } else if (isFunction2(source)) {
      if (cb) {
        getter = () => callWithErrorHandling2(source, instance, 2);
      } else {
        getter = () => {
          if (instance && instance.isUnmounted) {
            return;
          }
          if (cleanup) {
            cleanup();
          }
          return callWithAsyncErrorHandling2(
            source,
            instance,
            3,
            [onCleanup]
          );
        };
      }
    } else {
      getter = NOOP2;
      warnInvalidSource(source);
    }
    if (cb && deep) {
      const baseGetter = getter;
      getter = () => traverse2(baseGetter());
    }
    let cleanup;
    let onCleanup = (fn2) => {
      cleanup = effect6.onStop = () => {
        callWithErrorHandling2(fn2, instance, 4);
        cleanup = effect6.onStop = void 0;
      };
    };
    let ssrCleanup;
    if (isInSSRComponentSetup2) {
      onCleanup = NOOP2;
      if (!cb) {
        getter();
      } else if (immediate) {
        callWithAsyncErrorHandling2(cb, instance, 3, [
          getter(),
          isMultiSource ? [] : void 0,
          onCleanup
        ]);
      }
      if (flush === "sync") {
        const ctx = useSSRContext2();
        ssrCleanup = ctx.__watcherHandles || (ctx.__watcherHandles = []);
      } else {
        return NOOP2;
      }
    }
    let oldValue = isMultiSource ? new Array(source.length).fill(INITIAL_WATCHER_VALUE2) : INITIAL_WATCHER_VALUE2;
    const job = () => {
      if (!effect6.active) {
        return;
      }
      if (cb) {
        const newValue = effect6.run();
        if (deep || forceTrigger || (isMultiSource ? newValue.some((v, i) => hasChanged2(v, oldValue[i])) : hasChanged2(newValue, oldValue)) || false) {
          if (cleanup) {
            cleanup();
          }
          callWithAsyncErrorHandling2(cb, instance, 3, [
            newValue,
            oldValue === INITIAL_WATCHER_VALUE2 ? void 0 : isMultiSource && oldValue[0] === INITIAL_WATCHER_VALUE2 ? [] : oldValue,
            onCleanup
          ]);
          oldValue = newValue;
        }
      } else {
        effect6.run();
      }
    };
    job.allowRecurse = !!cb;
    let scheduler;
    if (flush === "sync") {
      scheduler = job;
    } else if (flush === "post") {
      scheduler = () => queuePostRenderEffect2(job, instance && instance.suspense);
    } else {
      job.pre = true;
      if (instance)
        job.id = instance.uid;
      scheduler = () => queueJob2(job);
    }
    const effect6 = new ReactiveEffect2(getter, scheduler);
    if (true) {
      effect6.onTrack = onTrack;
      effect6.onTrigger = onTrigger;
    }
    if (cb) {
      if (immediate) {
        job();
      } else {
        oldValue = effect6.run();
      }
    } else if (flush === "post") {
      queuePostRenderEffect2(
        effect6.run.bind(effect6),
        instance && instance.suspense
      );
    } else {
      effect6.run();
    }
    const unwatch = () => {
      effect6.stop();
      if (instance && instance.scope) {
        remove2(instance.scope.effects, effect6);
      }
    };
    if (ssrCleanup)
      ssrCleanup.push(unwatch);
    return unwatch;
  }
  function instanceWatch2(source, value, options) {
    const publicThis = this.proxy;
    const getter = isString2(source) ? source.includes(".") ? createPathGetter2(publicThis, source) : () => publicThis[source] : source.bind(publicThis, publicThis);
    let cb;
    if (isFunction2(value)) {
      cb = value;
    } else {
      cb = value.handler;
      options = value;
    }
    const cur = currentInstance2;
    setCurrentInstance2(this);
    const res = doWatch2(getter, cb.bind(publicThis), options);
    if (cur) {
      setCurrentInstance2(cur);
    } else {
      unsetCurrentInstance2();
    }
    return res;
  }
  function createPathGetter2(ctx, path) {
    const segments = path.split(".");
    return () => {
      let cur = ctx;
      for (let i = 0; i < segments.length && cur; i++) {
        cur = cur[segments[i]];
      }
      return cur;
    };
  }
  function traverse2(value, seen) {
    if (!isObject2(value) || value["__v_skip"]) {
      return value;
    }
    seen = seen || /* @__PURE__ */ new Set();
    if (seen.has(value)) {
      return value;
    }
    seen.add(value);
    if (isRef3(value)) {
      traverse2(value.value, seen);
    } else if (isArray2(value)) {
      for (let i = 0; i < value.length; i++) {
        traverse2(value[i], seen);
      }
    } else if (isSet2(value) || isMap2(value)) {
      value.forEach((v) => {
        traverse2(v, seen);
      });
    } else if (isPlainObject2(value)) {
      for (const key in value) {
        traverse2(value[key], seen);
      }
    }
    return value;
  }
  function withDirectives2(vnode, directives) {
    const internalInstance = currentRenderingInstance2;
    if (internalInstance === null) {
      warn4(`withDirectives can only be used inside render functions.`);
      return vnode;
    }
    const instance = getExposeProxy(internalInstance) || internalInstance.proxy;
    const bindings = vnode.dirs || (vnode.dirs = []);
    for (let i = 0; i < directives.length; i++) {
      let [dir, value, arg, modifiers = EMPTY_OBJ2] = directives[i];
      if (dir) {
        if (isFunction2(dir)) {
          dir = {
            mounted: dir,
            updated: dir
          };
        }
        if (dir.deep) {
          traverse2(value);
        }
        bindings.push({
          dir,
          instance,
          value,
          oldValue: void 0,
          arg,
          modifiers
        });
      }
    }
    return vnode;
  }
  var leaveCbKey2 = Symbol("_leaveCb");
  var enterCbKey3 = Symbol("_enterCb");
  function useTransitionState2() {
    const state = {
      isMounted: false,
      isLeaving: false,
      isUnmounting: false,
      leavingVNodes: /* @__PURE__ */ new Map()
    };
    onMounted2(() => {
      state.isMounted = true;
    });
    onBeforeUnmount2(() => {
      state.isUnmounting = true;
    });
    return state;
  }
  var TransitionHookValidator = [Function, Array];
  var BaseTransitionPropsValidators2 = {
    mode: String,
    appear: Boolean,
    persisted: Boolean,
    onBeforeEnter: TransitionHookValidator,
    onEnter: TransitionHookValidator,
    onAfterEnter: TransitionHookValidator,
    onEnterCancelled: TransitionHookValidator,
    onBeforeLeave: TransitionHookValidator,
    onLeave: TransitionHookValidator,
    onAfterLeave: TransitionHookValidator,
    onLeaveCancelled: TransitionHookValidator,
    onBeforeAppear: TransitionHookValidator,
    onAppear: TransitionHookValidator,
    onAfterAppear: TransitionHookValidator,
    onAppearCancelled: TransitionHookValidator
  };
  var BaseTransitionImpl = {
    name: `BaseTransition`,
    props: BaseTransitionPropsValidators2,
    setup(props, { slots }) {
      const instance = getCurrentInstance2();
      const state = useTransitionState2();
      let prevTransitionKey;
      return () => {
        const children = slots.default && getTransitionRawChildren2(slots.default(), true);
        if (!children || !children.length) {
          return;
        }
        let child = children[0];
        if (children.length > 1) {
          let hasFound = false;
          for (const c of children) {
            if (c.type !== Comment2) {
              if (hasFound) {
                warn4(
                  "<transition> can only be used on a single element or component. Use <transition-group> for lists."
                );
                break;
              }
              child = c;
              hasFound = true;
              if (false)
                break;
            }
          }
        }
        const rawProps = toRaw2(props);
        const { mode } = rawProps;
        if (mode && mode !== "in-out" && mode !== "out-in" && mode !== "default") {
          warn4(`invalid <transition> mode: ${mode}`);
        }
        if (state.isLeaving) {
          return emptyPlaceholder(child);
        }
        const innerChild = getKeepAliveChild(child);
        if (!innerChild) {
          return emptyPlaceholder(child);
        }
        const enterHooks = resolveTransitionHooks2(
          innerChild,
          rawProps,
          state,
          instance
        );
        setTransitionHooks2(innerChild, enterHooks);
        const oldChild = instance.subTree;
        const oldInnerChild = oldChild && getKeepAliveChild(oldChild);
        let transitionKeyChanged = false;
        const { getTransitionKey } = innerChild.type;
        if (getTransitionKey) {
          const key = getTransitionKey();
          if (prevTransitionKey === void 0) {
            prevTransitionKey = key;
          } else if (key !== prevTransitionKey) {
            prevTransitionKey = key;
            transitionKeyChanged = true;
          }
        }
        if (oldInnerChild && oldInnerChild.type !== Comment2 && (!isSameVNodeType2(innerChild, oldInnerChild) || transitionKeyChanged)) {
          const leavingHooks = resolveTransitionHooks2(
            oldInnerChild,
            rawProps,
            state,
            instance
          );
          setTransitionHooks2(oldInnerChild, leavingHooks);
          if (mode === "out-in") {
            state.isLeaving = true;
            leavingHooks.afterLeave = () => {
              state.isLeaving = false;
              if (instance.update.active !== false) {
                instance.update();
              }
            };
            return emptyPlaceholder(child);
          } else if (mode === "in-out" && innerChild.type !== Comment2) {
            leavingHooks.delayLeave = (el, earlyRemove, delayedLeave) => {
              const leavingVNodesCache = getLeavingNodesForType(
                state,
                oldInnerChild
              );
              leavingVNodesCache[String(oldInnerChild.key)] = oldInnerChild;
              el[leaveCbKey2] = () => {
                earlyRemove();
                el[leaveCbKey2] = void 0;
                delete enterHooks.delayedLeave;
              };
              enterHooks.delayedLeave = delayedLeave;
            };
          }
        }
        return child;
      };
    }
  };
  var BaseTransition2 = BaseTransitionImpl;
  function getLeavingNodesForType(state, vnode) {
    const { leavingVNodes } = state;
    let leavingVNodesCache = leavingVNodes.get(vnode.type);
    if (!leavingVNodesCache) {
      leavingVNodesCache = /* @__PURE__ */ Object.create(null);
      leavingVNodes.set(vnode.type, leavingVNodesCache);
    }
    return leavingVNodesCache;
  }
  function resolveTransitionHooks2(vnode, props, state, instance) {
    const {
      appear,
      mode,
      persisted = false,
      onBeforeEnter,
      onEnter,
      onAfterEnter,
      onEnterCancelled,
      onBeforeLeave,
      onLeave,
      onAfterLeave,
      onLeaveCancelled,
      onBeforeAppear,
      onAppear,
      onAfterAppear,
      onAppearCancelled
    } = props;
    const key = String(vnode.key);
    const leavingVNodesCache = getLeavingNodesForType(state, vnode);
    const callHook3 = (hook, args) => {
      hook && callWithAsyncErrorHandling2(
        hook,
        instance,
        9,
        args
      );
    };
    const callAsyncHook = (hook, args) => {
      const done = args[1];
      callHook3(hook, args);
      if (isArray2(hook)) {
        if (hook.every((hook2) => hook2.length <= 1))
          done();
      } else if (hook.length <= 1) {
        done();
      }
    };
    const hooks = {
      mode,
      persisted,
      beforeEnter(el) {
        let hook = onBeforeEnter;
        if (!state.isMounted) {
          if (appear) {
            hook = onBeforeAppear || onBeforeEnter;
          } else {
            return;
          }
        }
        if (el[leaveCbKey2]) {
          el[leaveCbKey2](
            true
          );
        }
        const leavingVNode = leavingVNodesCache[key];
        if (leavingVNode && isSameVNodeType2(vnode, leavingVNode) && leavingVNode.el[leaveCbKey2]) {
          leavingVNode.el[leaveCbKey2]();
        }
        callHook3(hook, [el]);
      },
      enter(el) {
        let hook = onEnter;
        let afterHook = onAfterEnter;
        let cancelHook = onEnterCancelled;
        if (!state.isMounted) {
          if (appear) {
            hook = onAppear || onEnter;
            afterHook = onAfterAppear || onAfterEnter;
            cancelHook = onAppearCancelled || onEnterCancelled;
          } else {
            return;
          }
        }
        let called = false;
        const done = el[enterCbKey3] = (cancelled) => {
          if (called)
            return;
          called = true;
          if (cancelled) {
            callHook3(cancelHook, [el]);
          } else {
            callHook3(afterHook, [el]);
          }
          if (hooks.delayedLeave) {
            hooks.delayedLeave();
          }
          el[enterCbKey3] = void 0;
        };
        if (hook) {
          callAsyncHook(hook, [el, done]);
        } else {
          done();
        }
      },
      leave(el, remove3) {
        const key2 = String(vnode.key);
        if (el[enterCbKey3]) {
          el[enterCbKey3](
            true
          );
        }
        if (state.isUnmounting) {
          return remove3();
        }
        callHook3(onBeforeLeave, [el]);
        let called = false;
        const done = el[leaveCbKey2] = (cancelled) => {
          if (called)
            return;
          called = true;
          remove3();
          if (cancelled) {
            callHook3(onLeaveCancelled, [el]);
          } else {
            callHook3(onAfterLeave, [el]);
          }
          el[leaveCbKey2] = void 0;
          if (leavingVNodesCache[key2] === vnode) {
            delete leavingVNodesCache[key2];
          }
        };
        leavingVNodesCache[key2] = vnode;
        if (onLeave) {
          callAsyncHook(onLeave, [el, done]);
        } else {
          done();
        }
      },
      clone(vnode2) {
        return resolveTransitionHooks2(vnode2, props, state, instance);
      }
    };
    return hooks;
  }
  function emptyPlaceholder(vnode) {
    if (isKeepAlive2(vnode)) {
      vnode = cloneVNode2(vnode);
      vnode.children = null;
      return vnode;
    }
  }
  function getKeepAliveChild(vnode) {
    return isKeepAlive2(vnode) ? vnode.component ? vnode.component.subTree : vnode.children ? vnode.children[0] : void 0 : vnode;
  }
  function setTransitionHooks2(vnode, hooks) {
    if (vnode.shapeFlag & 6 && vnode.component) {
      setTransitionHooks2(vnode.component.subTree, hooks);
    } else if (vnode.shapeFlag & 128) {
      vnode.ssContent.transition = hooks.clone(vnode.ssContent);
      vnode.ssFallback.transition = hooks.clone(vnode.ssFallback);
    } else {
      vnode.transition = hooks;
    }
  }
  function getTransitionRawChildren2(children, keepComment = false, parentKey) {
    let ret = [];
    let keyedFragmentCount = 0;
    for (let i = 0; i < children.length; i++) {
      let child = children[i];
      const key = parentKey == null ? child.key : String(parentKey) + String(child.key != null ? child.key : i);
      if (child.type === Fragment2) {
        if (child.patchFlag & 128)
          keyedFragmentCount++;
        ret = ret.concat(
          getTransitionRawChildren2(child.children, keepComment, key)
        );
      } else if (keepComment || child.type !== Comment2) {
        ret.push(key != null ? cloneVNode2(child, { key }) : child);
      }
    }
    if (keyedFragmentCount > 1) {
      for (let i = 0; i < ret.length; i++) {
        ret[i].patchFlag = -2;
      }
    }
    return ret;
  }
  var isKeepAlive2 = (vnode) => vnode.type.__isKeepAlive;
  function injectHook2(type, hook, target = currentInstance2, prepend = false) {
    if (target) {
      const hooks = target[type] || (target[type] = []);
      const wrappedHook = hook.__weh || (hook.__weh = (...args) => {
        if (target.isUnmounted) {
          return;
        }
        pauseTracking2();
        setCurrentInstance2(target);
        const res = callWithAsyncErrorHandling2(hook, target, type, args);
        unsetCurrentInstance2();
        resetTracking2();
        return res;
      });
      if (prepend) {
        hooks.unshift(wrappedHook);
      } else {
        hooks.push(wrappedHook);
      }
      return wrappedHook;
    } else if (true) {
      const apiName = toHandlerKey2(ErrorTypeStrings[type].replace(/ hook$/, ""));
      warn4(
        `${apiName} is called when there is no active component instance to be associated with. Lifecycle injection APIs can only be used during execution of setup(). If you are using async setup(), make sure to register lifecycle hooks before the first await statement.`
      );
    }
  }
  var createHook2 = (lifecycle) => (hook, target = currentInstance2) => (!isInSSRComponentSetup2 || lifecycle === "sp") && injectHook2(lifecycle, (...args) => hook(...args), target);
  var onBeforeMount2 = createHook2("bm");
  var onMounted2 = createHook2("m");
  var onBeforeUpdate2 = createHook2("bu");
  var onUpdated2 = createHook2("u");
  var onBeforeUnmount2 = createHook2("bum");
  var onUnmounted2 = createHook2("um");
  var onServerPrefetch2 = createHook2("sp");
  var onRenderTriggered2 = createHook2(
    "rtg"
  );
  var onRenderTracked2 = createHook2(
    "rtc"
  );
  function renderList2(source, renderItem, cache, index) {
    let ret;
    const cached = cache && cache[index];
    if (isArray2(source) || isString2(source)) {
      ret = new Array(source.length);
      for (let i = 0, l = source.length; i < l; i++) {
        ret[i] = renderItem(source[i], i, void 0, cached && cached[i]);
      }
    } else if (typeof source === "number") {
      if (!Number.isInteger(source)) {
        warn4(`The v-for range expect an integer value but got ${source}.`);
      }
      ret = new Array(source);
      for (let i = 0; i < source; i++) {
        ret[i] = renderItem(i + 1, i, void 0, cached && cached[i]);
      }
    } else if (isObject2(source)) {
      if (source[Symbol.iterator]) {
        ret = Array.from(
          source,
          (item, i) => renderItem(item, i, void 0, cached && cached[i])
        );
      } else {
        const keys = Object.keys(source);
        ret = new Array(keys.length);
        for (let i = 0, l = keys.length; i < l; i++) {
          const key = keys[i];
          ret[i] = renderItem(source[key], key, i, cached && cached[i]);
        }
      }
    } else {
      ret = [];
    }
    if (cache) {
      cache[index] = ret;
    }
    return ret;
  }
  var getPublicInstance2 = (i) => {
    if (!i)
      return null;
    if (isStatefulComponent2(i))
      return getExposeProxy(i) || i.proxy;
    return getPublicInstance2(i.parent);
  };
  var publicPropertiesMap2 = /* @__PURE__ */ extend2(/* @__PURE__ */ Object.create(null), {
    $: (i) => i,
    $el: (i) => i.vnode.el,
    $data: (i) => i.data,
    $props: (i) => true ? shallowReadonly2(i.props) : i.props,
    $attrs: (i) => true ? shallowReadonly2(i.attrs) : i.attrs,
    $slots: (i) => true ? shallowReadonly2(i.slots) : i.slots,
    $refs: (i) => true ? shallowReadonly2(i.refs) : i.refs,
    $parent: (i) => getPublicInstance2(i.parent),
    $root: (i) => getPublicInstance2(i.root),
    $emit: (i) => i.emit,
    $options: (i) => true ? resolveMergedOptions2(i) : i.type,
    $forceUpdate: (i) => i.f || (i.f = () => queueJob2(i.update)),
    $nextTick: (i) => i.n || (i.n = nextTick2.bind(i.proxy)),
    $watch: (i) => true ? instanceWatch2.bind(i) : NOOP2
  });
  var isReservedPrefix2 = (key) => key === "_" || key === "$";
  var hasSetupBinding2 = (state, key) => state !== EMPTY_OBJ2 && !state.__isScriptSetup && hasOwn2(state, key);
  var PublicInstanceProxyHandlers2 = {
    get({ _: instance }, key) {
      const { ctx, setupState, data, props, accessCache, type, appContext } = instance;
      if (key === "__isVue") {
        return true;
      }
      let normalizedProps;
      if (key[0] !== "$") {
        const n = accessCache[key];
        if (n !== void 0) {
          switch (n) {
            case 1:
              return setupState[key];
            case 2:
              return data[key];
            case 4:
              return ctx[key];
            case 3:
              return props[key];
          }
        } else if (hasSetupBinding2(setupState, key)) {
          accessCache[key] = 1;
          return setupState[key];
        } else if (data !== EMPTY_OBJ2 && hasOwn2(data, key)) {
          accessCache[key] = 2;
          return data[key];
        } else if ((normalizedProps = instance.propsOptions[0]) && hasOwn2(normalizedProps, key)) {
          accessCache[key] = 3;
          return props[key];
        } else if (ctx !== EMPTY_OBJ2 && hasOwn2(ctx, key)) {
          accessCache[key] = 4;
          return ctx[key];
        } else if (shouldCacheAccess2) {
          accessCache[key] = 0;
        }
      }
      const publicGetter = publicPropertiesMap2[key];
      let cssModule, globalProperties;
      if (publicGetter) {
        if (key === "$attrs") {
          track2(instance, "get", key);
          markAttrsAccessed2();
        } else if (key === "$slots") {
          track2(instance, "get", key);
        }
        return publicGetter(instance);
      } else if ((cssModule = type.__cssModules) && (cssModule = cssModule[key])) {
        return cssModule;
      } else if (ctx !== EMPTY_OBJ2 && hasOwn2(ctx, key)) {
        accessCache[key] = 4;
        return ctx[key];
      } else if (globalProperties = appContext.config.globalProperties, hasOwn2(globalProperties, key)) {
        {
          return globalProperties[key];
        }
      } else if (currentRenderingInstance2 && (!isString2(key) || key.indexOf("__v") !== 0)) {
        if (data !== EMPTY_OBJ2 && isReservedPrefix2(key[0]) && hasOwn2(data, key)) {
          warn4(
            `Property ${JSON.stringify(
              key
            )} must be accessed via $data because it starts with a reserved character ("$" or "_") and is not proxied on the render context.`
          );
        } else if (instance === currentRenderingInstance2) {
          warn4(
            `Property ${JSON.stringify(key)} was accessed during render but is not defined on instance.`
          );
        }
      }
    },
    set({ _: instance }, key, value) {
      const { data, setupState, ctx } = instance;
      if (hasSetupBinding2(setupState, key)) {
        setupState[key] = value;
        return true;
      } else if (setupState.__isScriptSetup && hasOwn2(setupState, key)) {
        warn4(`Cannot mutate <script setup> binding "${key}" from Options API.`);
        return false;
      } else if (data !== EMPTY_OBJ2 && hasOwn2(data, key)) {
        data[key] = value;
        return true;
      } else if (hasOwn2(instance.props, key)) {
        warn4(`Attempting to mutate prop "${key}". Props are readonly.`);
        return false;
      }
      if (key[0] === "$" && key.slice(1) in instance) {
        warn4(
          `Attempting to mutate public property "${key}". Properties starting with $ are reserved and readonly.`
        );
        return false;
      } else {
        if (key in instance.appContext.config.globalProperties) {
          Object.defineProperty(ctx, key, {
            enumerable: true,
            configurable: true,
            value
          });
        } else {
          ctx[key] = value;
        }
      }
      return true;
    },
    has({
      _: { data, setupState, accessCache, ctx, appContext, propsOptions }
    }, key) {
      let normalizedProps;
      return !!accessCache[key] || data !== EMPTY_OBJ2 && hasOwn2(data, key) || hasSetupBinding2(setupState, key) || (normalizedProps = propsOptions[0]) && hasOwn2(normalizedProps, key) || hasOwn2(ctx, key) || hasOwn2(publicPropertiesMap2, key) || hasOwn2(appContext.config.globalProperties, key);
    },
    defineProperty(target, key, descriptor) {
      if (descriptor.get != null) {
        target._.accessCache[key] = 0;
      } else if (hasOwn2(descriptor, "value")) {
        this.set(target, key, descriptor.value, null);
      }
      return Reflect.defineProperty(target, key, descriptor);
    }
  };
  if (true) {
    PublicInstanceProxyHandlers2.ownKeys = (target) => {
      warn4(
        `Avoid app logic that relies on enumerating keys on a component instance. The keys will be empty in production mode to avoid performance overhead.`
      );
      return Reflect.ownKeys(target);
    };
  }
  function normalizePropsOrEmits2(props) {
    return isArray2(props) ? props.reduce(
      (normalized, p2) => (normalized[p2] = null, normalized),
      {}
    ) : props;
  }
  var shouldCacheAccess2 = true;
  function resolveMergedOptions2(instance) {
    const base = instance.type;
    const { mixins, extends: extendsOptions } = base;
    const {
      mixins: globalMixins,
      optionsCache: cache,
      config: { optionMergeStrategies }
    } = instance.appContext;
    const cached = cache.get(base);
    let resolved;
    if (cached) {
      resolved = cached;
    } else if (!globalMixins.length && !mixins && !extendsOptions) {
      {
        resolved = base;
      }
    } else {
      resolved = {};
      if (globalMixins.length) {
        globalMixins.forEach(
          (m) => mergeOptions2(resolved, m, optionMergeStrategies, true)
        );
      }
      mergeOptions2(resolved, base, optionMergeStrategies);
    }
    if (isObject2(base)) {
      cache.set(base, resolved);
    }
    return resolved;
  }
  function mergeOptions2(to, from, strats, asMixin = false) {
    const { mixins, extends: extendsOptions } = from;
    if (extendsOptions) {
      mergeOptions2(to, extendsOptions, strats, true);
    }
    if (mixins) {
      mixins.forEach(
        (m) => mergeOptions2(to, m, strats, true)
      );
    }
    for (const key in from) {
      if (asMixin && key === "expose") {
        warn4(
          `"expose" option is ignored when declared in mixins or extends. It should only be declared in the base component itself.`
        );
      } else {
        const strat = internalOptionMergeStrats2[key] || strats && strats[key];
        to[key] = strat ? strat(to[key], from[key]) : from[key];
      }
    }
    return to;
  }
  var internalOptionMergeStrats2 = {
    data: mergeDataFn2,
    props: mergeEmitsOrPropsOptions2,
    emits: mergeEmitsOrPropsOptions2,
    methods: mergeObjectOptions2,
    computed: mergeObjectOptions2,
    beforeCreate: mergeAsArray2,
    created: mergeAsArray2,
    beforeMount: mergeAsArray2,
    mounted: mergeAsArray2,
    beforeUpdate: mergeAsArray2,
    updated: mergeAsArray2,
    beforeDestroy: mergeAsArray2,
    beforeUnmount: mergeAsArray2,
    destroyed: mergeAsArray2,
    unmounted: mergeAsArray2,
    activated: mergeAsArray2,
    deactivated: mergeAsArray2,
    errorCaptured: mergeAsArray2,
    serverPrefetch: mergeAsArray2,
    components: mergeObjectOptions2,
    directives: mergeObjectOptions2,
    watch: mergeWatchOptions2,
    provide: mergeDataFn2,
    inject: mergeInject2
  };
  function mergeDataFn2(to, from) {
    if (!from) {
      return to;
    }
    if (!to) {
      return from;
    }
    return function mergedDataFn() {
      return extend2(
        isFunction2(to) ? to.call(this, this) : to,
        isFunction2(from) ? from.call(this, this) : from
      );
    };
  }
  function mergeInject2(to, from) {
    return mergeObjectOptions2(normalizeInject2(to), normalizeInject2(from));
  }
  function normalizeInject2(raw) {
    if (isArray2(raw)) {
      const res = {};
      for (let i = 0; i < raw.length; i++) {
        res[raw[i]] = raw[i];
      }
      return res;
    }
    return raw;
  }
  function mergeAsArray2(to, from) {
    return to ? [...new Set([].concat(to, from))] : from;
  }
  function mergeObjectOptions2(to, from) {
    return to ? extend2(/* @__PURE__ */ Object.create(null), to, from) : from;
  }
  function mergeEmitsOrPropsOptions2(to, from) {
    if (to) {
      if (isArray2(to) && isArray2(from)) {
        return [.../* @__PURE__ */ new Set([...to, ...from])];
      }
      return extend2(
        /* @__PURE__ */ Object.create(null),
        normalizePropsOrEmits2(to),
        normalizePropsOrEmits2(from != null ? from : {})
      );
    } else {
      return from;
    }
  }
  function mergeWatchOptions2(to, from) {
    if (!to)
      return from;
    if (!from)
      return to;
    const merged = extend2(/* @__PURE__ */ Object.create(null), to);
    for (const key in from) {
      merged[key] = mergeAsArray2(to[key], from[key]);
    }
    return merged;
  }
  function createAppContext2() {
    return {
      app: null,
      config: {
        isNativeTag: NO2,
        performance: false,
        globalProperties: {},
        optionMergeStrategies: {},
        errorHandler: void 0,
        warnHandler: void 0,
        compilerOptions: {}
      },
      mixins: [],
      components: {},
      directives: {},
      provides: /* @__PURE__ */ Object.create(null),
      optionsCache: /* @__PURE__ */ new WeakMap(),
      propsCache: /* @__PURE__ */ new WeakMap(),
      emitsCache: /* @__PURE__ */ new WeakMap()
    };
  }
  var currentApp2 = null;
  function inject2(key, defaultValue, treatDefaultAsFactory = false) {
    const instance = currentInstance2 || currentRenderingInstance2;
    if (instance || currentApp2) {
      const provides = instance ? instance.parent == null ? instance.vnode.appContext && instance.vnode.appContext.provides : instance.parent.provides : currentApp2._context.provides;
      if (provides && key in provides) {
        return provides[key];
      } else if (arguments.length > 1) {
        return treatDefaultAsFactory && isFunction2(defaultValue) ? defaultValue.call(instance && instance.proxy) : defaultValue;
      } else if (true) {
        warn4(`injection "${String(key)}" not found.`);
      }
    } else if (true) {
      warn4(`inject() can only be used inside setup() or functional components.`);
    }
  }
  var queuePostRenderEffect2 = queueEffectWithSuspense2;
  var isTeleport2 = (type) => type.__isTeleport;
  var Fragment2 = Symbol.for("v-fgt");
  var Text2 = Symbol.for("v-txt");
  var Comment2 = Symbol.for("v-cmt");
  var Static2 = Symbol.for("v-stc");
  var blockStack2 = [];
  var currentBlock2 = null;
  function openBlock2(disableTracking = false) {
    blockStack2.push(currentBlock2 = disableTracking ? null : []);
  }
  function closeBlock2() {
    blockStack2.pop();
    currentBlock2 = blockStack2[blockStack2.length - 1] || null;
  }
  var isBlockTreeEnabled2 = 1;
  function setupBlock2(vnode) {
    vnode.dynamicChildren = isBlockTreeEnabled2 > 0 ? currentBlock2 || EMPTY_ARR2 : null;
    closeBlock2();
    if (isBlockTreeEnabled2 > 0 && currentBlock2) {
      currentBlock2.push(vnode);
    }
    return vnode;
  }
  function createElementBlock2(type, props, children, patchFlag, dynamicProps, shapeFlag) {
    return setupBlock2(
      createBaseVNode2(
        type,
        props,
        children,
        patchFlag,
        dynamicProps,
        shapeFlag,
        true
      )
    );
  }
  function createBlock2(type, props, children, patchFlag, dynamicProps) {
    return setupBlock2(
      createVNode2(
        type,
        props,
        children,
        patchFlag,
        dynamicProps,
        true
      )
    );
  }
  function isVNode2(value) {
    return value ? value.__v_isVNode === true : false;
  }
  function isSameVNodeType2(n1, n2) {
    if (n2.shapeFlag & 6 && hmrDirtyComponents2.has(n2.type)) {
      n1.shapeFlag &= ~256;
      n2.shapeFlag &= ~512;
      return false;
    }
    return n1.type === n2.type && n1.key === n2.key;
  }
  var vnodeArgsTransformer2;
  var createVNodeWithArgsTransform2 = (...args) => {
    return _createVNode2(
      ...vnodeArgsTransformer2 ? vnodeArgsTransformer2(args, currentRenderingInstance2) : args
    );
  };
  var InternalObjectKey = `__vInternal`;
  var normalizeKey2 = ({ key }) => key != null ? key : null;
  var normalizeRef2 = ({
    ref: ref3,
    ref_key,
    ref_for
  }) => {
    if (typeof ref3 === "number") {
      ref3 = "" + ref3;
    }
    return ref3 != null ? isString2(ref3) || isRef3(ref3) || isFunction2(ref3) ? { i: currentRenderingInstance2, r: ref3, k: ref_key, f: !!ref_for } : ref3 : null;
  };
  function createBaseVNode2(type, props = null, children = null, patchFlag = 0, dynamicProps = null, shapeFlag = type === Fragment2 ? 0 : 1, isBlockNode = false, needFullChildrenNormalization = false) {
    const vnode = {
      __v_isVNode: true,
      __v_skip: true,
      type,
      props,
      key: props && normalizeKey2(props),
      ref: props && normalizeRef2(props),
      scopeId: currentScopeId2,
      slotScopeIds: null,
      children,
      component: null,
      suspense: null,
      ssContent: null,
      ssFallback: null,
      dirs: null,
      transition: null,
      el: null,
      anchor: null,
      target: null,
      targetAnchor: null,
      staticCount: 0,
      shapeFlag,
      patchFlag,
      dynamicProps,
      dynamicChildren: null,
      appContext: null,
      ctx: currentRenderingInstance2
    };
    if (needFullChildrenNormalization) {
      normalizeChildren2(vnode, children);
      if (shapeFlag & 128) {
        type.normalize(vnode);
      }
    } else if (children) {
      vnode.shapeFlag |= isString2(children) ? 8 : 16;
    }
    if (vnode.key !== vnode.key) {
      warn4(`VNode created with invalid key (NaN). VNode type:`, vnode.type);
    }
    if (isBlockTreeEnabled2 > 0 && !isBlockNode && currentBlock2 && (vnode.patchFlag > 0 || shapeFlag & 6) && vnode.patchFlag !== 32) {
      currentBlock2.push(vnode);
    }
    return vnode;
  }
  var createVNode2 = true ? createVNodeWithArgsTransform2 : _createVNode2;
  function _createVNode2(type, props = null, children = null, patchFlag = 0, dynamicProps = null, isBlockNode = false) {
    if (!type || type === NULL_DYNAMIC_COMPONENT2) {
      if (!type) {
        warn4(`Invalid vnode type when creating vnode: ${type}.`);
      }
      type = Comment2;
    }
    if (isVNode2(type)) {
      const cloned = cloneVNode2(
        type,
        props,
        true
      );
      if (children) {
        normalizeChildren2(cloned, children);
      }
      if (isBlockTreeEnabled2 > 0 && !isBlockNode && currentBlock2) {
        if (cloned.shapeFlag & 6) {
          currentBlock2[currentBlock2.indexOf(type)] = cloned;
        } else {
          currentBlock2.push(cloned);
        }
      }
      cloned.patchFlag |= -2;
      return cloned;
    }
    if (isClassComponent2(type)) {
      type = type.__vccOpts;
    }
    if (props) {
      props = guardReactiveProps2(props);
      let { class: klass, style } = props;
      if (klass && !isString2(klass)) {
        props.class = normalizeClass2(klass);
      }
      if (isObject2(style)) {
        if (isProxy2(style) && !isArray2(style)) {
          style = extend2({}, style);
        }
        props.style = normalizeStyle2(style);
      }
    }
    const shapeFlag = isString2(type) ? 1 : isSuspense2(type) ? 128 : isTeleport2(type) ? 64 : isObject2(type) ? 4 : isFunction2(type) ? 2 : 0;
    if (shapeFlag & 4 && isProxy2(type)) {
      type = toRaw2(type);
      warn4(
        `Vue received a Component that was made a reactive object. This can lead to unnecessary performance overhead and should be avoided by marking the component with \`markRaw\` or using \`shallowRef\` instead of \`ref\`.`,
        `
Component that was made reactive: `,
        type
      );
    }
    return createBaseVNode2(
      type,
      props,
      children,
      patchFlag,
      dynamicProps,
      shapeFlag,
      isBlockNode,
      true
    );
  }
  function guardReactiveProps2(props) {
    if (!props)
      return null;
    return isProxy2(props) || InternalObjectKey in props ? extend2({}, props) : props;
  }
  function cloneVNode2(vnode, extraProps, mergeRef = false) {
    const { props, ref: ref3, patchFlag, children } = vnode;
    const mergedProps = extraProps ? mergeProps2(props || {}, extraProps) : props;
    const cloned = {
      __v_isVNode: true,
      __v_skip: true,
      type: vnode.type,
      props: mergedProps,
      key: mergedProps && normalizeKey2(mergedProps),
      ref: extraProps && extraProps.ref ? mergeRef && ref3 ? isArray2(ref3) ? ref3.concat(normalizeRef2(extraProps)) : [ref3, normalizeRef2(extraProps)] : normalizeRef2(extraProps) : ref3,
      scopeId: vnode.scopeId,
      slotScopeIds: vnode.slotScopeIds,
      children: patchFlag === -1 && isArray2(children) ? children.map(deepCloneVNode2) : children,
      target: vnode.target,
      targetAnchor: vnode.targetAnchor,
      staticCount: vnode.staticCount,
      shapeFlag: vnode.shapeFlag,
      patchFlag: extraProps && vnode.type !== Fragment2 ? patchFlag === -1 ? 16 : patchFlag | 16 : patchFlag,
      dynamicProps: vnode.dynamicProps,
      dynamicChildren: vnode.dynamicChildren,
      appContext: vnode.appContext,
      dirs: vnode.dirs,
      transition: vnode.transition,
      component: vnode.component,
      suspense: vnode.suspense,
      ssContent: vnode.ssContent && cloneVNode2(vnode.ssContent),
      ssFallback: vnode.ssFallback && cloneVNode2(vnode.ssFallback),
      el: vnode.el,
      anchor: vnode.anchor,
      ctx: vnode.ctx,
      ce: vnode.ce
    };
    return cloned;
  }
  function deepCloneVNode2(vnode) {
    const cloned = cloneVNode2(vnode);
    if (isArray2(vnode.children)) {
      cloned.children = vnode.children.map(deepCloneVNode2);
    }
    return cloned;
  }
  function createTextVNode2(text = " ", flag = 0) {
    return createVNode2(Text2, null, text, flag);
  }
  function createCommentVNode2(text = "", asBlock = false) {
    return asBlock ? (openBlock2(), createBlock2(Comment2, null, text)) : createVNode2(Comment2, null, text);
  }
  function normalizeChildren2(vnode, children) {
    let type = 0;
    const { shapeFlag } = vnode;
    if (children == null) {
      children = null;
    } else if (isArray2(children)) {
      type = 16;
    } else if (typeof children === "object") {
      if (shapeFlag & (1 | 64)) {
        const slot = children.default;
        if (slot) {
          slot._c && (slot._d = false);
          normalizeChildren2(vnode, slot());
          slot._c && (slot._d = true);
        }
        return;
      } else {
        type = 32;
        const slotFlag = children._;
        if (!slotFlag && !(InternalObjectKey in children)) {
          children._ctx = currentRenderingInstance2;
        } else if (slotFlag === 3 && currentRenderingInstance2) {
          if (currentRenderingInstance2.slots._ === 1) {
            children._ = 1;
          } else {
            children._ = 2;
            vnode.patchFlag |= 1024;
          }
        }
      }
    } else if (isFunction2(children)) {
      children = { default: children, _ctx: currentRenderingInstance2 };
      type = 32;
    } else {
      children = String(children);
      if (shapeFlag & 64) {
        type = 16;
        children = [createTextVNode2(children)];
      } else {
        type = 8;
      }
    }
    vnode.children = children;
    vnode.shapeFlag |= type;
  }
  function mergeProps2(...args) {
    const ret = {};
    for (let i = 0; i < args.length; i++) {
      const toMerge = args[i];
      for (const key in toMerge) {
        if (key === "class") {
          if (ret.class !== toMerge.class) {
            ret.class = normalizeClass2([ret.class, toMerge.class]);
          }
        } else if (key === "style") {
          ret.style = normalizeStyle2([ret.style, toMerge.style]);
        } else if (isOn2(key)) {
          const existing = ret[key];
          const incoming = toMerge[key];
          if (incoming && existing !== incoming && !(isArray2(existing) && existing.includes(incoming))) {
            ret[key] = existing ? [].concat(existing, incoming) : incoming;
          }
        } else if (key !== "") {
          ret[key] = toMerge[key];
        }
      }
    }
    return ret;
  }
  var emptyAppContext2 = createAppContext2();
  var currentInstance2 = null;
  var getCurrentInstance2 = () => currentInstance2 || currentRenderingInstance2;
  var internalSetCurrentInstance2;
  var globalCurrentInstanceSetters;
  var settersKey = "__VUE_INSTANCE_SETTERS__";
  {
    if (!(globalCurrentInstanceSetters = getGlobalThis2()[settersKey])) {
      globalCurrentInstanceSetters = getGlobalThis2()[settersKey] = [];
    }
    globalCurrentInstanceSetters.push((i) => currentInstance2 = i);
    internalSetCurrentInstance2 = (instance) => {
      if (globalCurrentInstanceSetters.length > 1) {
        globalCurrentInstanceSetters.forEach((s) => s(instance));
      } else {
        globalCurrentInstanceSetters[0](instance);
      }
    };
  }
  var setCurrentInstance2 = (instance) => {
    internalSetCurrentInstance2(instance);
    instance.scope.on();
  };
  var unsetCurrentInstance2 = () => {
    currentInstance2 && currentInstance2.scope.off();
    internalSetCurrentInstance2(null);
  };
  function isStatefulComponent2(instance) {
    return instance.vnode.shapeFlag & 4;
  }
  var isInSSRComponentSetup2 = false;
  function getExposeProxy(instance) {
    if (instance.exposed) {
      return instance.exposeProxy || (instance.exposeProxy = new Proxy(proxyRefs2(markRaw2(instance.exposed)), {
        get(target, key) {
          if (key in target) {
            return target[key];
          } else if (key in publicPropertiesMap2) {
            return publicPropertiesMap2[key](instance);
          }
        },
        has(target, key) {
          return key in target || key in publicPropertiesMap2;
        }
      }));
    }
  }
  var classifyRE2 = /(?:^|[-_])(\w)/g;
  var classify2 = (str) => str.replace(classifyRE2, (c) => c.toUpperCase()).replace(/[-_]/g, "");
  function getComponentName2(Component, includeInferred = true) {
    return isFunction2(Component) ? Component.displayName || Component.name : Component.name || includeInferred && Component.__name;
  }
  function formatComponentName2(instance, Component, isRoot = false) {
    let name = getComponentName2(Component);
    if (!name && Component.__file) {
      const match = Component.__file.match(/([^/\\]+)\.\w+$/);
      if (match) {
        name = match[1];
      }
    }
    if (!name && instance && instance.parent) {
      const inferFromRegistry = (registry) => {
        for (const key in registry) {
          if (registry[key] === Component) {
            return key;
          }
        }
      };
      name = inferFromRegistry(
        instance.components || instance.parent.type.components
      ) || inferFromRegistry(instance.appContext.components);
    }
    return name ? classify2(name) : isRoot ? `App` : `Anonymous`;
  }
  function isClassComponent2(value) {
    return isFunction2(value) && "__vccOpts" in value;
  }
  var computed4 = (getterOrOptions, debugOptions) => {
    return computed3(getterOrOptions, debugOptions, isInSSRComponentSetup2);
  };
  function h2(type, propsOrChildren, children) {
    const l = arguments.length;
    if (l === 2) {
      if (isObject2(propsOrChildren) && !isArray2(propsOrChildren)) {
        if (isVNode2(propsOrChildren)) {
          return createVNode2(type, null, [propsOrChildren]);
        }
        return createVNode2(type, propsOrChildren);
      } else {
        return createVNode2(type, null, propsOrChildren);
      }
    } else {
      if (l > 3) {
        children = Array.prototype.slice.call(arguments, 2);
      } else if (l === 3 && isVNode2(children)) {
        children = [children];
      }
      return createVNode2(type, propsOrChildren, children);
    }
  }
  var ssrContextKey2 = Symbol.for("v-scx");
  var useSSRContext2 = () => {
    {
      const ctx = inject2(ssrContextKey2);
      if (!ctx) {
        warn4(
          `Server rendering context not provided. Make sure to only call useSSRContext() conditionally in the server build.`
        );
      }
      return ctx;
    }
  };
  function isShallow3(value) {
    return !!(value && value["__v_isShallow"]);
  }
  function initCustomFormatter2() {
    if (typeof window === "undefined") {
      return;
    }
    const vueStyle = { style: "color:#3ba776" };
    const numberStyle = { style: "color:#0b1bc9" };
    const stringStyle = { style: "color:#b62e24" };
    const keywordStyle = { style: "color:#9d288c" };
    const formatter = {
      header(obj) {
        if (!isObject2(obj)) {
          return null;
        }
        if (obj.__isVue) {
          return ["div", vueStyle, `VueInstance`];
        } else if (isRef3(obj)) {
          return [
            "div",
            {},
            ["span", vueStyle, genRefFlag(obj)],
            "<",
            formatValue(obj.value),
            `>`
          ];
        } else if (isReactive2(obj)) {
          return [
            "div",
            {},
            ["span", vueStyle, isShallow3(obj) ? "ShallowReactive" : "Reactive"],
            "<",
            formatValue(obj),
            `>${isReadonly2(obj) ? ` (readonly)` : ``}`
          ];
        } else if (isReadonly2(obj)) {
          return [
            "div",
            {},
            ["span", vueStyle, isShallow3(obj) ? "ShallowReadonly" : "Readonly"],
            "<",
            formatValue(obj),
            ">"
          ];
        }
        return null;
      },
      hasBody(obj) {
        return obj && obj.__isVue;
      },
      body(obj) {
        if (obj && obj.__isVue) {
          return [
            "div",
            {},
            ...formatInstance(obj.$)
          ];
        }
      }
    };
    function formatInstance(instance) {
      const blocks = [];
      if (instance.type.props && instance.props) {
        blocks.push(createInstanceBlock("props", toRaw2(instance.props)));
      }
      if (instance.setupState !== EMPTY_OBJ2) {
        blocks.push(createInstanceBlock("setup", instance.setupState));
      }
      if (instance.data !== EMPTY_OBJ2) {
        blocks.push(createInstanceBlock("data", toRaw2(instance.data)));
      }
      const computed5 = extractKeys(instance, "computed");
      if (computed5) {
        blocks.push(createInstanceBlock("computed", computed5));
      }
      const injected = extractKeys(instance, "inject");
      if (injected) {
        blocks.push(createInstanceBlock("injected", injected));
      }
      blocks.push([
        "div",
        {},
        [
          "span",
          {
            style: keywordStyle.style + ";opacity:0.66"
          },
          "$ (internal): "
        ],
        ["object", { object: instance }]
      ]);
      return blocks;
    }
    function createInstanceBlock(type, target) {
      target = extend2({}, target);
      if (!Object.keys(target).length) {
        return ["span", {}];
      }
      return [
        "div",
        { style: "line-height:1.25em;margin-bottom:0.6em" },
        [
          "div",
          {
            style: "color:#476582"
          },
          type
        ],
        [
          "div",
          {
            style: "padding-left:1.25em"
          },
          ...Object.keys(target).map((key) => {
            return [
              "div",
              {},
              ["span", keywordStyle, key + ": "],
              formatValue(target[key], false)
            ];
          })
        ]
      ];
    }
    function formatValue(v, asRaw = true) {
      if (typeof v === "number") {
        return ["span", numberStyle, v];
      } else if (typeof v === "string") {
        return ["span", stringStyle, JSON.stringify(v)];
      } else if (typeof v === "boolean") {
        return ["span", keywordStyle, v];
      } else if (isObject2(v)) {
        return ["object", { object: asRaw ? toRaw2(v) : v }];
      } else {
        return ["span", stringStyle, String(v)];
      }
    }
    function extractKeys(instance, type) {
      const Comp = instance.type;
      if (isFunction2(Comp)) {
        return;
      }
      const extracted = {};
      for (const key in instance.ctx) {
        if (isKeyOfType(Comp, key, type)) {
          extracted[key] = instance.ctx[key];
        }
      }
      return extracted;
    }
    function isKeyOfType(Comp, key, type) {
      const opts = Comp[type];
      if (isArray2(opts) && opts.includes(key) || isObject2(opts) && key in opts) {
        return true;
      }
      if (Comp.extends && isKeyOfType(Comp.extends, key, type)) {
        return true;
      }
      if (Comp.mixins && Comp.mixins.some((m) => isKeyOfType(m, key, type))) {
        return true;
      }
    }
    function genRefFlag(v) {
      if (isShallow3(v)) {
        return `ShallowRef`;
      }
      if (v.effect) {
        return `ComputedRef`;
      }
      return `Ref`;
    }
    if (window.devtoolsFormatters) {
      window.devtoolsFormatters.push(formatter);
    } else {
      window.devtoolsFormatters = [formatter];
    }
  }

  // node_modules/@vue/runtime-dom/dist/runtime-dom.esm-bundler.js
  var TRANSITION = "transition";
  var ANIMATION = "animation";
  var vtcKey2 = Symbol("_vtc");
  var Transition = (props, { slots }) => h2(BaseTransition2, resolveTransitionProps(props), slots);
  Transition.displayName = "Transition";
  var DOMTransitionPropsValidators = {
    name: String,
    type: String,
    css: {
      type: Boolean,
      default: true
    },
    duration: [String, Number, Object],
    enterFromClass: String,
    enterActiveClass: String,
    enterToClass: String,
    appearFromClass: String,
    appearActiveClass: String,
    appearToClass: String,
    leaveFromClass: String,
    leaveActiveClass: String,
    leaveToClass: String
  };
  var TransitionPropsValidators = Transition.props = /* @__PURE__ */ extend2(
    {},
    BaseTransitionPropsValidators2,
    DOMTransitionPropsValidators
  );
  var callHook2 = (hook, args = []) => {
    if (isArray2(hook)) {
      hook.forEach((h22) => h22(...args));
    } else if (hook) {
      hook(...args);
    }
  };
  var hasExplicitCallback = (hook) => {
    return hook ? isArray2(hook) ? hook.some((h22) => h22.length > 1) : hook.length > 1 : false;
  };
  function resolveTransitionProps(rawProps) {
    const baseProps = {};
    for (const key in rawProps) {
      if (!(key in DOMTransitionPropsValidators)) {
        baseProps[key] = rawProps[key];
      }
    }
    if (rawProps.css === false) {
      return baseProps;
    }
    const {
      name = "v",
      type,
      duration,
      enterFromClass = `${name}-enter-from`,
      enterActiveClass = `${name}-enter-active`,
      enterToClass = `${name}-enter-to`,
      appearFromClass = enterFromClass,
      appearActiveClass = enterActiveClass,
      appearToClass = enterToClass,
      leaveFromClass = `${name}-leave-from`,
      leaveActiveClass = `${name}-leave-active`,
      leaveToClass = `${name}-leave-to`
    } = rawProps;
    const durations = normalizeDuration(duration);
    const enterDuration = durations && durations[0];
    const leaveDuration = durations && durations[1];
    const {
      onBeforeEnter,
      onEnter,
      onEnterCancelled,
      onLeave,
      onLeaveCancelled,
      onBeforeAppear = onBeforeEnter,
      onAppear = onEnter,
      onAppearCancelled = onEnterCancelled
    } = baseProps;
    const finishEnter = (el, isAppear, done) => {
      removeTransitionClass(el, isAppear ? appearToClass : enterToClass);
      removeTransitionClass(el, isAppear ? appearActiveClass : enterActiveClass);
      done && done();
    };
    const finishLeave = (el, done) => {
      el._isLeaving = false;
      removeTransitionClass(el, leaveFromClass);
      removeTransitionClass(el, leaveToClass);
      removeTransitionClass(el, leaveActiveClass);
      done && done();
    };
    const makeEnterHook = (isAppear) => {
      return (el, done) => {
        const hook = isAppear ? onAppear : onEnter;
        const resolve = () => finishEnter(el, isAppear, done);
        callHook2(hook, [el, resolve]);
        nextFrame(() => {
          removeTransitionClass(el, isAppear ? appearFromClass : enterFromClass);
          addTransitionClass(el, isAppear ? appearToClass : enterToClass);
          if (!hasExplicitCallback(hook)) {
            whenTransitionEnds(el, type, enterDuration, resolve);
          }
        });
      };
    };
    return extend2(baseProps, {
      onBeforeEnter(el) {
        callHook2(onBeforeEnter, [el]);
        addTransitionClass(el, enterFromClass);
        addTransitionClass(el, enterActiveClass);
      },
      onBeforeAppear(el) {
        callHook2(onBeforeAppear, [el]);
        addTransitionClass(el, appearFromClass);
        addTransitionClass(el, appearActiveClass);
      },
      onEnter: makeEnterHook(false),
      onAppear: makeEnterHook(true),
      onLeave(el, done) {
        el._isLeaving = true;
        const resolve = () => finishLeave(el, done);
        addTransitionClass(el, leaveFromClass);
        forceReflow();
        addTransitionClass(el, leaveActiveClass);
        nextFrame(() => {
          if (!el._isLeaving) {
            return;
          }
          removeTransitionClass(el, leaveFromClass);
          addTransitionClass(el, leaveToClass);
          if (!hasExplicitCallback(onLeave)) {
            whenTransitionEnds(el, type, leaveDuration, resolve);
          }
        });
        callHook2(onLeave, [el, resolve]);
      },
      onEnterCancelled(el) {
        finishEnter(el, false);
        callHook2(onEnterCancelled, [el]);
      },
      onAppearCancelled(el) {
        finishEnter(el, true);
        callHook2(onAppearCancelled, [el]);
      },
      onLeaveCancelled(el) {
        finishLeave(el);
        callHook2(onLeaveCancelled, [el]);
      }
    });
  }
  function normalizeDuration(duration) {
    if (duration == null) {
      return null;
    } else if (isObject2(duration)) {
      return [NumberOf(duration.enter), NumberOf(duration.leave)];
    } else {
      const n = NumberOf(duration);
      return [n, n];
    }
  }
  function NumberOf(val) {
    const res = toNumber2(val);
    if (true) {
      assertNumber2(res, "<transition> explicit duration");
    }
    return res;
  }
  function addTransitionClass(el, cls) {
    cls.split(/\s+/).forEach((c) => c && el.classList.add(c));
    (el[vtcKey2] || (el[vtcKey2] = /* @__PURE__ */ new Set())).add(cls);
  }
  function removeTransitionClass(el, cls) {
    cls.split(/\s+/).forEach((c) => c && el.classList.remove(c));
    const _vtc = el[vtcKey2];
    if (_vtc) {
      _vtc.delete(cls);
      if (!_vtc.size) {
        el[vtcKey2] = void 0;
      }
    }
  }
  function nextFrame(cb) {
    requestAnimationFrame(() => {
      requestAnimationFrame(cb);
    });
  }
  var endId = 0;
  function whenTransitionEnds(el, expectedType, explicitTimeout, resolve) {
    const id = el._endId = ++endId;
    const resolveIfNotStale = () => {
      if (id === el._endId) {
        resolve();
      }
    };
    if (explicitTimeout) {
      return setTimeout(resolveIfNotStale, explicitTimeout);
    }
    const { type, timeout, propCount } = getTransitionInfo(el, expectedType);
    if (!type) {
      return resolve();
    }
    const endEvent = type + "end";
    let ended = 0;
    const end2 = () => {
      el.removeEventListener(endEvent, onEnd);
      resolveIfNotStale();
    };
    const onEnd = (e) => {
      if (e.target === el && ++ended >= propCount) {
        end2();
      }
    };
    setTimeout(() => {
      if (ended < propCount) {
        end2();
      }
    }, timeout + 1);
    el.addEventListener(endEvent, onEnd);
  }
  function getTransitionInfo(el, expectedType) {
    const styles = window.getComputedStyle(el);
    const getStyleProperties = (key) => (styles[key] || "").split(", ");
    const transitionDelays = getStyleProperties(`${TRANSITION}Delay`);
    const transitionDurations = getStyleProperties(`${TRANSITION}Duration`);
    const transitionTimeout = getTimeout(transitionDelays, transitionDurations);
    const animationDelays = getStyleProperties(`${ANIMATION}Delay`);
    const animationDurations = getStyleProperties(`${ANIMATION}Duration`);
    const animationTimeout = getTimeout(animationDelays, animationDurations);
    let type = null;
    let timeout = 0;
    let propCount = 0;
    if (expectedType === TRANSITION) {
      if (transitionTimeout > 0) {
        type = TRANSITION;
        timeout = transitionTimeout;
        propCount = transitionDurations.length;
      }
    } else if (expectedType === ANIMATION) {
      if (animationTimeout > 0) {
        type = ANIMATION;
        timeout = animationTimeout;
        propCount = animationDurations.length;
      }
    } else {
      timeout = Math.max(transitionTimeout, animationTimeout);
      type = timeout > 0 ? transitionTimeout > animationTimeout ? TRANSITION : ANIMATION : null;
      propCount = type ? type === TRANSITION ? transitionDurations.length : animationDurations.length : 0;
    }
    const hasTransform = type === TRANSITION && /\b(transform|all)(,|$)/.test(
      getStyleProperties(`${TRANSITION}Property`).toString()
    );
    return {
      type,
      timeout,
      propCount,
      hasTransform
    };
  }
  function getTimeout(delays, durations) {
    while (delays.length < durations.length) {
      delays = delays.concat(delays);
    }
    return Math.max(...durations.map((d, i) => toMs(d) + toMs(delays[i])));
  }
  function toMs(s) {
    if (s === "auto")
      return 0;
    return Number(s.slice(0, -1).replace(",", ".")) * 1e3;
  }
  function forceReflow() {
    return document.body.offsetHeight;
  }
  var vShowOldKey = Symbol("_vod");
  var vShow2 = {
    beforeMount(el, { value }, { transition }) {
      el[vShowOldKey] = el.style.display === "none" ? "" : el.style.display;
      if (transition && value) {
        transition.beforeEnter(el);
      } else {
        setDisplay2(el, value);
      }
    },
    mounted(el, { value }, { transition }) {
      if (transition && value) {
        transition.enter(el);
      }
    },
    updated(el, { value, oldValue }, { transition }) {
      if (!value === !oldValue)
        return;
      if (transition) {
        if (value) {
          transition.beforeEnter(el);
          setDisplay2(el, true);
          transition.enter(el);
        } else {
          transition.leave(el, () => {
            setDisplay2(el, false);
          });
        }
      } else {
        setDisplay2(el, value);
      }
    },
    beforeUnmount(el, { value }) {
      setDisplay2(el, value);
    }
  };
  function setDisplay2(el, value) {
    el.style.display = value ? el[vShowOldKey] : "none";
  }
  function addEventListener2(el, event, handler, options) {
    el.addEventListener(event, handler, options);
  }
  var veiKey2 = Symbol("_vei");
  var positionMap = /* @__PURE__ */ new WeakMap();
  var newPositionMap = /* @__PURE__ */ new WeakMap();
  var moveCbKey2 = Symbol("_moveCb");
  var enterCbKey4 = Symbol("_enterCb");
  var TransitionGroupImpl = {
    name: "TransitionGroup",
    props: /* @__PURE__ */ extend2({}, TransitionPropsValidators, {
      tag: String,
      moveClass: String
    }),
    setup(props, { slots }) {
      const instance = getCurrentInstance2();
      const state = useTransitionState2();
      let prevChildren;
      let children;
      onUpdated2(() => {
        if (!prevChildren.length) {
          return;
        }
        const moveClass = props.moveClass || `${props.name || "v"}-move`;
        if (!hasCSSTransform(
          prevChildren[0].el,
          instance.vnode.el,
          moveClass
        )) {
          return;
        }
        prevChildren.forEach(callPendingCbs);
        prevChildren.forEach(recordPosition);
        const movedChildren = prevChildren.filter(applyTranslation);
        forceReflow();
        movedChildren.forEach((c) => {
          const el = c.el;
          const style = el.style;
          addTransitionClass(el, moveClass);
          style.transform = style.webkitTransform = style.transitionDuration = "";
          const cb = el[moveCbKey2] = (e) => {
            if (e && e.target !== el) {
              return;
            }
            if (!e || /transform$/.test(e.propertyName)) {
              el.removeEventListener("transitionend", cb);
              el[moveCbKey2] = null;
              removeTransitionClass(el, moveClass);
            }
          };
          el.addEventListener("transitionend", cb);
        });
      });
      return () => {
        const rawProps = toRaw2(props);
        const cssTransitionProps = resolveTransitionProps(rawProps);
        let tag = rawProps.tag || Fragment2;
        prevChildren = children;
        children = slots.default ? getTransitionRawChildren2(slots.default()) : [];
        for (let i = 0; i < children.length; i++) {
          const child = children[i];
          if (child.key != null) {
            setTransitionHooks2(
              child,
              resolveTransitionHooks2(child, cssTransitionProps, state, instance)
            );
          } else if (true) {
            warn4(`<TransitionGroup> children must be keyed.`);
          }
        }
        if (prevChildren) {
          for (let i = 0; i < prevChildren.length; i++) {
            const child = prevChildren[i];
            setTransitionHooks2(
              child,
              resolveTransitionHooks2(child, cssTransitionProps, state, instance)
            );
            positionMap.set(child, child.el.getBoundingClientRect());
          }
        }
        return createVNode2(tag, null, children);
      };
    }
  };
  var removeMode = (props) => delete props.mode;
  /* @__PURE__ */ removeMode(TransitionGroupImpl.props);
  function callPendingCbs(c) {
    const el = c.el;
    if (el[moveCbKey2]) {
      el[moveCbKey2]();
    }
    if (el[enterCbKey4]) {
      el[enterCbKey4]();
    }
  }
  function recordPosition(c) {
    newPositionMap.set(c, c.el.getBoundingClientRect());
  }
  function applyTranslation(c) {
    const oldPos = positionMap.get(c);
    const newPos = newPositionMap.get(c);
    const dx = oldPos.left - newPos.left;
    const dy = oldPos.top - newPos.top;
    if (dx || dy) {
      const s = c.el.style;
      s.transform = s.webkitTransform = `translate(${dx}px,${dy}px)`;
      s.transitionDuration = "0s";
      return c;
    }
  }
  function hasCSSTransform(el, root, moveClass) {
    const clone = el.cloneNode();
    const _vtc = el[vtcKey2];
    if (_vtc) {
      _vtc.forEach((cls) => {
        cls.split(/\s+/).forEach((c) => c && clone.classList.remove(c));
      });
    }
    moveClass.split(/\s+/).forEach((c) => c && clone.classList.add(c));
    clone.style.display = "none";
    const container = root.nodeType === 1 ? root : root.parentNode;
    container.appendChild(clone);
    const { hasTransform } = getTransitionInfo(clone);
    container.removeChild(clone);
    return hasTransform;
  }
  var getModelAssigner = (vnode) => {
    const fn2 = vnode.props["onUpdate:modelValue"] || false;
    return isArray2(fn2) ? (value) => invokeArrayFns2(fn2, value) : fn2;
  };
  function onCompositionStart(e) {
    e.target.composing = true;
  }
  function onCompositionEnd(e) {
    const target = e.target;
    if (target.composing) {
      target.composing = false;
      target.dispatchEvent(new Event("input"));
    }
  }
  var assignKey2 = Symbol("_assign");
  var vModelText = {
    created(el, { modifiers: { lazy, trim, number } }, vnode) {
      el[assignKey2] = getModelAssigner(vnode);
      const castToNumber = number || vnode.props && vnode.props.type === "number";
      addEventListener2(el, lazy ? "change" : "input", (e) => {
        if (e.target.composing)
          return;
        let domValue = el.value;
        if (trim) {
          domValue = domValue.trim();
        }
        if (castToNumber) {
          domValue = looseToNumber2(domValue);
        }
        el[assignKey2](domValue);
      });
      if (trim) {
        addEventListener2(el, "change", () => {
          el.value = el.value.trim();
        });
      }
      if (!lazy) {
        addEventListener2(el, "compositionstart", onCompositionStart);
        addEventListener2(el, "compositionend", onCompositionEnd);
        addEventListener2(el, "change", onCompositionEnd);
      }
    },
    mounted(el, { value }) {
      el.value = value == null ? "" : value;
    },
    beforeUpdate(el, { value, modifiers: { lazy, trim, number } }, vnode) {
      el[assignKey2] = getModelAssigner(vnode);
      if (el.composing)
        return;
      const elValue = number || el.type === "number" ? looseToNumber2(el.value) : el.value;
      const newValue = value == null ? "" : value;
      if (elValue === newValue) {
        return;
      }
      if (document.activeElement === el && el.type !== "range") {
        if (lazy) {
          return;
        }
        if (trim && el.value.trim() === newValue) {
          return;
        }
      }
      el.value = newValue;
    }
  };
  var systemModifiers2 = ["ctrl", "shift", "alt", "meta"];
  var modifierGuards2 = {
    stop: (e) => e.stopPropagation(),
    prevent: (e) => e.preventDefault(),
    self: (e) => e.target !== e.currentTarget,
    ctrl: (e) => !e.ctrlKey,
    shift: (e) => !e.shiftKey,
    alt: (e) => !e.altKey,
    meta: (e) => !e.metaKey,
    left: (e) => "button" in e && e.button !== 0,
    middle: (e) => "button" in e && e.button !== 1,
    right: (e) => "button" in e && e.button !== 2,
    exact: (e, modifiers) => systemModifiers2.some((m) => e[`${m}Key`] && !modifiers.includes(m))
  };
  var withModifiers2 = (fn2, modifiers) => {
    return (event, ...args) => {
      for (let i = 0; i < modifiers.length; i++) {
        const guard = modifierGuards2[modifiers[i]];
        if (guard && guard(event, modifiers))
          return;
      }
      return fn2(event, ...args);
    };
  };

  // node_modules/vue/dist/vue.runtime.esm-bundler.js
  function initDev2() {
    {
      initCustomFormatter2();
    }
  }
  if (true) {
    initDev2();
  }

  // sfc-script:/home/frappe/yefri-bench/apps/frappe/frappe/public/js/frappe/file_uploader/ProgressRing.vue?type=script
  var ProgressRing_default = {
    __name: "ProgressRing",
    props: {
      primary: String,
      secondary: String,
      radius: Number,
      progress: Number,
      stroke: Number
    },
    setup(__props, { expose: __expose }) {
      __expose();
      const props = __props;
      let normalizedRadius = ref2(props.radius - props.stroke * 2);
      let circumference = ref2(normalizedRadius.value * 2 * Math.PI);
      let strokeDashoffset = computed4(() => {
        return circumference.value - props.progress / 100 * circumference.value;
      });
      const __returned__ = { props, get normalizedRadius() {
        return normalizedRadius;
      }, set normalizedRadius(v) {
        normalizedRadius = v;
      }, get circumference() {
        return circumference;
      }, set circumference(v) {
        circumference = v;
      }, get strokeDashoffset() {
        return strokeDashoffset;
      }, set strokeDashoffset(v) {
        strokeDashoffset = v;
      }, computed: computed4, ref: ref2 };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  };

  // sfc-template:/home/frappe/yefri-bench/apps/frappe/frappe/public/js/frappe/file_uploader/ProgressRing.vue?type=template
  var _hoisted_1 = ["height", "width"];
  var _hoisted_2 = ["stroke-dasharray", "stroke-width", "r", "cx", "cy"];
  var _hoisted_3 = ["stroke-dasharray", "stroke-width", "r", "cx", "cy"];
  var _hoisted_4 = ["x", "y"];
  function render(_ctx, _cache, $props, $setup, $data, $options) {
    return openBlock2(), createElementBlock2("svg", {
      height: $props.radius * 2,
      width: $props.radius * 2
    }, [
      createBaseVNode2("circle", {
        "stroke-dasharray": $setup.circumference + " " + $setup.circumference,
        style: normalizeStyle2({
          stroke: $props.secondary,
          strokeDashoffset: 0
        }),
        "stroke-width": $props.stroke,
        fill: "transparent",
        r: $setup.normalizedRadius,
        cx: $props.radius,
        cy: $props.radius
      }, null, 12, _hoisted_2),
      createBaseVNode2("circle", {
        "stroke-dasharray": $setup.circumference + " " + $setup.circumference,
        style: normalizeStyle2({
          stroke: $props.primary,
          strokeDashoffset: $setup.strokeDashoffset
        }),
        "stroke-width": $props.stroke,
        fill: "transparent",
        r: $setup.normalizedRadius,
        cx: $props.radius,
        cy: $props.radius
      }, null, 12, _hoisted_3),
      createBaseVNode2("text", {
        "dominant-baseline": "middle",
        "text-anchor": "middle",
        x: $props.radius,
        y: $props.radius,
        style: normalizeStyle2({
          color: "var(--text-color)",
          fontSize: "var(--text-xs)",
          fontWeight: "var(--text-bold)"
        })
      }, toDisplayString2($props.progress) + "% ", 13, _hoisted_4)
    ], 8, _hoisted_1);
  }

  // frappe/public/js/frappe/file_uploader/ProgressRing.vue
  ProgressRing_default.render = render;
  ProgressRing_default.__file = "frappe/public/js/frappe/file_uploader/ProgressRing.vue";
  ProgressRing_default.__scopeId = "data-v-e4881e80";
  var ProgressRing_default2 = ProgressRing_default;

  // sfc-script:/home/frappe/yefri-bench/apps/frappe/frappe/public/js/frappe/file_uploader/FilePreview.vue?type=script
  var FilePreview_default = {
    __name: "FilePreview",
    props: {
      file: Object
    },
    emits: ["toggle_optimize", "toggle_private", "toggle_image_cropper", "remove"],
    setup(__props, { expose: __expose, emit: __emit }) {
      __expose();
      let emit2 = __emit;
      const props = __props;
      let src = ref2(null);
      let optimize = ref2(props.file.optimize);
      let file_size = computed4(() => {
        return frappe.form.formatters.FileSize(props.file.file_obj.size);
      });
      let is_private = computed4(() => {
        return props.file.doc ? props.file.doc.is_private : props.file.private;
      });
      let uploaded = computed4(() => {
        return props.file.request_succeeded;
      });
      let is_image = computed4(() => {
        return props.file.file_obj.type.startsWith("image");
      });
      let is_optimizable = computed4(() => {
        let is_svg = props.file.file_obj.type == "image/svg+xml";
        return is_image.value && !is_svg && !uploaded.value && !props.file.failed;
      });
      let is_cropable = computed4(() => {
        let croppable_types = ["image/jpeg", "image/png"];
        return !uploaded.value && !props.file.uploading && !props.file.failed && croppable_types.includes(props.file.file_obj.type);
      });
      let progress = computed4(() => {
        let value = Math.round(props.file.progress * 100 / props.file.total);
        if (isNaN(value)) {
          value = 0;
        }
        return value;
      });
      onMounted2(() => {
        if (is_image.value) {
          if (window.FileReader) {
            let fr = new FileReader();
            fr.onload = () => src.value = fr.result;
            fr.readAsDataURL(props.file.file_obj);
          }
        }
      });
      const __returned__ = { get emit() {
        return emit2;
      }, set emit(v) {
        emit2 = v;
      }, props, get src() {
        return src;
      }, set src(v) {
        src = v;
      }, get optimize() {
        return optimize;
      }, set optimize(v) {
        optimize = v;
      }, get file_size() {
        return file_size;
      }, set file_size(v) {
        file_size = v;
      }, get is_private() {
        return is_private;
      }, set is_private(v) {
        is_private = v;
      }, get uploaded() {
        return uploaded;
      }, set uploaded(v) {
        uploaded = v;
      }, get is_image() {
        return is_image;
      }, set is_image(v) {
        is_image = v;
      }, get is_optimizable() {
        return is_optimizable;
      }, set is_optimizable(v) {
        is_optimizable = v;
      }, get is_cropable() {
        return is_cropable;
      }, set is_cropable(v) {
        is_cropable = v;
      }, get progress() {
        return progress;
      }, set progress(v) {
        progress = v;
      }, ref: ref2, onMounted: onMounted2, computed: computed4, ProgressRing: ProgressRing_default2 };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  };

  // sfc-template:/home/frappe/yefri-bench/apps/frappe/frappe/public/js/frappe/file_uploader/FilePreview.vue?type=template
  var _hoisted_12 = { class: "file-preview" };
  var _hoisted_22 = { class: "file-icon" };
  var _hoisted_32 = ["src", "alt"];
  var _hoisted_42 = ["innerHTML"];
  var _hoisted_5 = ["href"];
  var _hoisted_6 = { class: "file-name" };
  var _hoisted_7 = {
    key: 1,
    class: "file-name"
  };
  var _hoisted_8 = { class: "file-size" };
  var _hoisted_9 = { class: "flex config-area" };
  var _hoisted_10 = {
    key: 0,
    class: "frappe-checkbox"
  };
  var _hoisted_11 = ["checked"];
  var _hoisted_122 = { class: "frappe-checkbox" };
  var _hoisted_13 = ["checked"];
  var _hoisted_14 = {
    key: 0,
    class: "file-error text-danger"
  };
  var _hoisted_15 = { class: "file-actions" };
  var _hoisted_16 = ["innerHTML"];
  var _hoisted_17 = ["innerHTML"];
  var _hoisted_18 = { class: "file-action-buttons" };
  var _hoisted_19 = ["innerHTML"];
  var _hoisted_20 = ["innerHTML"];
  function render2(_ctx, _cache, $props, $setup, $data, $options) {
    return openBlock2(), createElementBlock2("div", _hoisted_12, [
      createBaseVNode2("div", _hoisted_22, [
        $setup.is_image ? (openBlock2(), createElementBlock2("img", {
          key: 0,
          src: $setup.src,
          alt: $props.file.name
        }, null, 8, _hoisted_32)) : (openBlock2(), createElementBlock2("div", {
          key: 1,
          class: "fallback",
          innerHTML: _ctx.frappe.utils.icon("file", "md")
        }, null, 8, _hoisted_42))
      ]),
      createBaseVNode2("div", null, [
        createBaseVNode2("div", null, [
          $props.file.doc ? (openBlock2(), createElementBlock2("a", {
            key: 0,
            class: "flex",
            href: $props.file.doc.file_url,
            target: "_blank"
          }, [
            createBaseVNode2("span", _hoisted_6, toDisplayString2($props.file.name), 1)
          ], 8, _hoisted_5)) : (openBlock2(), createElementBlock2("span", _hoisted_7, toDisplayString2($props.file.name), 1))
        ]),
        createBaseVNode2("div", null, [
          createBaseVNode2("span", _hoisted_8, toDisplayString2($setup.file_size), 1)
        ]),
        createBaseVNode2("div", _hoisted_9, [
          $setup.is_optimizable ? (openBlock2(), createElementBlock2("label", _hoisted_10, [
            createBaseVNode2("input", {
              type: "checkbox",
              checked: $setup.optimize,
              onChange: _cache[0] || (_cache[0] = ($event) => $setup.emit("toggle_optimize"))
            }, null, 40, _hoisted_11),
            createTextVNode2(toDisplayString2(_ctx.__("Optimize")), 1)
          ])) : createCommentVNode2("v-if", true),
          createBaseVNode2("label", _hoisted_122, [
            createBaseVNode2("input", {
              type: "checkbox",
              checked: $props.file.private,
              onChange: _cache[1] || (_cache[1] = ($event) => $setup.emit("toggle_private"))
            }, null, 40, _hoisted_13),
            createTextVNode2(toDisplayString2(_ctx.__("Private")), 1)
          ])
        ]),
        createBaseVNode2("div", null, [
          $props.file.error_message ? (openBlock2(), createElementBlock2("span", _hoisted_14, toDisplayString2($props.file.error_message), 1)) : createCommentVNode2("v-if", true)
        ])
      ]),
      createBaseVNode2("div", _hoisted_15, [
        withDirectives2(createVNode2($setup["ProgressRing"], {
          primary: "var(--primary-color)",
          secondary: "var(--gray-200)",
          radius: 24,
          progress: $setup.progress,
          stroke: 3
        }, null, 8, ["progress"]), [
          [vShow2, $props.file.uploading && !$setup.uploaded && !$props.file.failed]
        ]),
        $setup.uploaded ? (openBlock2(), createElementBlock2("div", {
          key: 0,
          innerHTML: _ctx.frappe.utils.icon("solid-success", "lg")
        }, null, 8, _hoisted_16)) : createCommentVNode2("v-if", true),
        $props.file.failed ? (openBlock2(), createElementBlock2("div", {
          key: 1,
          innerHTML: _ctx.frappe.utils.icon("solid-error", "lg")
        }, null, 8, _hoisted_17)) : createCommentVNode2("v-if", true),
        createBaseVNode2("div", _hoisted_18, [
          $setup.is_cropable ? (openBlock2(), createElementBlock2("button", {
            key: 0,
            class: "btn btn-crop muted",
            onClick: _cache[2] || (_cache[2] = ($event) => $setup.emit("toggle_image_cropper")),
            innerHTML: _ctx.frappe.utils.icon("crop", "md")
          }, null, 8, _hoisted_19)) : createCommentVNode2("v-if", true),
          !$setup.uploaded && !$props.file.uploading && !$props.file.failed ? (openBlock2(), createElementBlock2("button", {
            key: 1,
            class: "btn muted",
            onClick: _cache[3] || (_cache[3] = ($event) => $setup.emit("remove")),
            innerHTML: _ctx.frappe.utils.icon("delete", "md")
          }, null, 8, _hoisted_20)) : createCommentVNode2("v-if", true)
        ])
      ])
    ]);
  }

  // frappe/public/js/frappe/file_uploader/FilePreview.vue
  FilePreview_default.render = render2;
  FilePreview_default.__file = "frappe/public/js/frappe/file_uploader/FilePreview.vue";
  FilePreview_default.__scopeId = "data-v-d6847533";
  var FilePreview_default2 = FilePreview_default;

  // node_modules/@popperjs/core/lib/enums.js
  var top = "top";
  var bottom = "bottom";
  var right = "right";
  var left = "left";
  var auto = "auto";
  var basePlacements = [top, bottom, right, left];
  var start = "start";
  var end = "end";
  var clippingParents = "clippingParents";
  var viewport = "viewport";
  var popper = "popper";
  var reference = "reference";
  var variationPlacements = /* @__PURE__ */ basePlacements.reduce(function(acc, placement) {
    return acc.concat([placement + "-" + start, placement + "-" + end]);
  }, []);
  var placements = /* @__PURE__ */ [].concat(basePlacements, [auto]).reduce(function(acc, placement) {
    return acc.concat([placement, placement + "-" + start, placement + "-" + end]);
  }, []);
  var beforeRead = "beforeRead";
  var read = "read";
  var afterRead = "afterRead";
  var beforeMain = "beforeMain";
  var main = "main";
  var afterMain = "afterMain";
  var beforeWrite = "beforeWrite";
  var write = "write";
  var afterWrite = "afterWrite";
  var modifierPhases = [beforeRead, read, afterRead, beforeMain, main, afterMain, beforeWrite, write, afterWrite];

  // node_modules/@popperjs/core/lib/dom-utils/getNodeName.js
  function getNodeName(element) {
    return element ? (element.nodeName || "").toLowerCase() : null;
  }

  // node_modules/@popperjs/core/lib/dom-utils/getWindow.js
  function getWindow(node) {
    if (node == null) {
      return window;
    }
    if (node.toString() !== "[object Window]") {
      var ownerDocument = node.ownerDocument;
      return ownerDocument ? ownerDocument.defaultView || window : window;
    }
    return node;
  }

  // node_modules/@popperjs/core/lib/dom-utils/instanceOf.js
  function isElement(node) {
    var OwnElement = getWindow(node).Element;
    return node instanceof OwnElement || node instanceof Element;
  }
  function isHTMLElement(node) {
    var OwnElement = getWindow(node).HTMLElement;
    return node instanceof OwnElement || node instanceof HTMLElement;
  }
  function isShadowRoot(node) {
    if (typeof ShadowRoot === "undefined") {
      return false;
    }
    var OwnElement = getWindow(node).ShadowRoot;
    return node instanceof OwnElement || node instanceof ShadowRoot;
  }

  // node_modules/@popperjs/core/lib/modifiers/applyStyles.js
  function applyStyles(_ref) {
    var state = _ref.state;
    Object.keys(state.elements).forEach(function(name) {
      var style = state.styles[name] || {};
      var attributes = state.attributes[name] || {};
      var element = state.elements[name];
      if (!isHTMLElement(element) || !getNodeName(element)) {
        return;
      }
      Object.assign(element.style, style);
      Object.keys(attributes).forEach(function(name2) {
        var value = attributes[name2];
        if (value === false) {
          element.removeAttribute(name2);
        } else {
          element.setAttribute(name2, value === true ? "" : value);
        }
      });
    });
  }
  function effect3(_ref2) {
    var state = _ref2.state;
    var initialStyles = {
      popper: {
        position: state.options.strategy,
        left: "0",
        top: "0",
        margin: "0"
      },
      arrow: {
        position: "absolute"
      },
      reference: {}
    };
    Object.assign(state.elements.popper.style, initialStyles.popper);
    state.styles = initialStyles;
    if (state.elements.arrow) {
      Object.assign(state.elements.arrow.style, initialStyles.arrow);
    }
    return function() {
      Object.keys(state.elements).forEach(function(name) {
        var element = state.elements[name];
        var attributes = state.attributes[name] || {};
        var styleProperties = Object.keys(state.styles.hasOwnProperty(name) ? state.styles[name] : initialStyles[name]);
        var style = styleProperties.reduce(function(style2, property) {
          style2[property] = "";
          return style2;
        }, {});
        if (!isHTMLElement(element) || !getNodeName(element)) {
          return;
        }
        Object.assign(element.style, style);
        Object.keys(attributes).forEach(function(attribute) {
          element.removeAttribute(attribute);
        });
      });
    };
  }
  var applyStyles_default = {
    name: "applyStyles",
    enabled: true,
    phase: "write",
    fn: applyStyles,
    effect: effect3,
    requires: ["computeStyles"]
  };

  // node_modules/@popperjs/core/lib/utils/getBasePlacement.js
  function getBasePlacement(placement) {
    return placement.split("-")[0];
  }

  // node_modules/@popperjs/core/lib/utils/math.js
  var max = Math.max;
  var min = Math.min;
  var round = Math.round;

  // node_modules/@popperjs/core/lib/utils/userAgent.js
  function getUAString() {
    var uaData = navigator.userAgentData;
    if (uaData != null && uaData.brands && Array.isArray(uaData.brands)) {
      return uaData.brands.map(function(item) {
        return item.brand + "/" + item.version;
      }).join(" ");
    }
    return navigator.userAgent;
  }

  // node_modules/@popperjs/core/lib/dom-utils/isLayoutViewport.js
  function isLayoutViewport() {
    return !/^((?!chrome|android).)*safari/i.test(getUAString());
  }

  // node_modules/@popperjs/core/lib/dom-utils/getBoundingClientRect.js
  function getBoundingClientRect(element, includeScale, isFixedStrategy) {
    if (includeScale === void 0) {
      includeScale = false;
    }
    if (isFixedStrategy === void 0) {
      isFixedStrategy = false;
    }
    var clientRect = element.getBoundingClientRect();
    var scaleX = 1;
    var scaleY = 1;
    if (includeScale && isHTMLElement(element)) {
      scaleX = element.offsetWidth > 0 ? round(clientRect.width) / element.offsetWidth || 1 : 1;
      scaleY = element.offsetHeight > 0 ? round(clientRect.height) / element.offsetHeight || 1 : 1;
    }
    var _ref = isElement(element) ? getWindow(element) : window, visualViewport = _ref.visualViewport;
    var addVisualOffsets = !isLayoutViewport() && isFixedStrategy;
    var x = (clientRect.left + (addVisualOffsets && visualViewport ? visualViewport.offsetLeft : 0)) / scaleX;
    var y = (clientRect.top + (addVisualOffsets && visualViewport ? visualViewport.offsetTop : 0)) / scaleY;
    var width = clientRect.width / scaleX;
    var height = clientRect.height / scaleY;
    return {
      width,
      height,
      top: y,
      right: x + width,
      bottom: y + height,
      left: x,
      x,
      y
    };
  }

  // node_modules/@popperjs/core/lib/dom-utils/getLayoutRect.js
  function getLayoutRect(element) {
    var clientRect = getBoundingClientRect(element);
    var width = element.offsetWidth;
    var height = element.offsetHeight;
    if (Math.abs(clientRect.width - width) <= 1) {
      width = clientRect.width;
    }
    if (Math.abs(clientRect.height - height) <= 1) {
      height = clientRect.height;
    }
    return {
      x: element.offsetLeft,
      y: element.offsetTop,
      width,
      height
    };
  }

  // node_modules/@popperjs/core/lib/dom-utils/contains.js
  function contains(parent, child) {
    var rootNode = child.getRootNode && child.getRootNode();
    if (parent.contains(child)) {
      return true;
    } else if (rootNode && isShadowRoot(rootNode)) {
      var next = child;
      do {
        if (next && parent.isSameNode(next)) {
          return true;
        }
        next = next.parentNode || next.host;
      } while (next);
    }
    return false;
  }

  // node_modules/@popperjs/core/lib/dom-utils/getComputedStyle.js
  function getComputedStyle(element) {
    return getWindow(element).getComputedStyle(element);
  }

  // node_modules/@popperjs/core/lib/dom-utils/isTableElement.js
  function isTableElement(element) {
    return ["table", "td", "th"].indexOf(getNodeName(element)) >= 0;
  }

  // node_modules/@popperjs/core/lib/dom-utils/getDocumentElement.js
  function getDocumentElement(element) {
    return ((isElement(element) ? element.ownerDocument : element.document) || window.document).documentElement;
  }

  // node_modules/@popperjs/core/lib/dom-utils/getParentNode.js
  function getParentNode(element) {
    if (getNodeName(element) === "html") {
      return element;
    }
    return element.assignedSlot || element.parentNode || (isShadowRoot(element) ? element.host : null) || getDocumentElement(element);
  }

  // node_modules/@popperjs/core/lib/dom-utils/getOffsetParent.js
  function getTrueOffsetParent(element) {
    if (!isHTMLElement(element) || getComputedStyle(element).position === "fixed") {
      return null;
    }
    return element.offsetParent;
  }
  function getContainingBlock(element) {
    var isFirefox = /firefox/i.test(getUAString());
    var isIE = /Trident/i.test(getUAString());
    if (isIE && isHTMLElement(element)) {
      var elementCss = getComputedStyle(element);
      if (elementCss.position === "fixed") {
        return null;
      }
    }
    var currentNode = getParentNode(element);
    if (isShadowRoot(currentNode)) {
      currentNode = currentNode.host;
    }
    while (isHTMLElement(currentNode) && ["html", "body"].indexOf(getNodeName(currentNode)) < 0) {
      var css = getComputedStyle(currentNode);
      if (css.transform !== "none" || css.perspective !== "none" || css.contain === "paint" || ["transform", "perspective"].indexOf(css.willChange) !== -1 || isFirefox && css.willChange === "filter" || isFirefox && css.filter && css.filter !== "none") {
        return currentNode;
      } else {
        currentNode = currentNode.parentNode;
      }
    }
    return null;
  }
  function getOffsetParent(element) {
    var window2 = getWindow(element);
    var offsetParent = getTrueOffsetParent(element);
    while (offsetParent && isTableElement(offsetParent) && getComputedStyle(offsetParent).position === "static") {
      offsetParent = getTrueOffsetParent(offsetParent);
    }
    if (offsetParent && (getNodeName(offsetParent) === "html" || getNodeName(offsetParent) === "body" && getComputedStyle(offsetParent).position === "static")) {
      return window2;
    }
    return offsetParent || getContainingBlock(element) || window2;
  }

  // node_modules/@popperjs/core/lib/utils/getMainAxisFromPlacement.js
  function getMainAxisFromPlacement(placement) {
    return ["top", "bottom"].indexOf(placement) >= 0 ? "x" : "y";
  }

  // node_modules/@popperjs/core/lib/utils/within.js
  function within(min2, value, max2) {
    return max(min2, min(value, max2));
  }
  function withinMaxClamp(min2, value, max2) {
    var v = within(min2, value, max2);
    return v > max2 ? max2 : v;
  }

  // node_modules/@popperjs/core/lib/utils/getFreshSideObject.js
  function getFreshSideObject() {
    return {
      top: 0,
      right: 0,
      bottom: 0,
      left: 0
    };
  }

  // node_modules/@popperjs/core/lib/utils/mergePaddingObject.js
  function mergePaddingObject(paddingObject) {
    return Object.assign({}, getFreshSideObject(), paddingObject);
  }

  // node_modules/@popperjs/core/lib/utils/expandToHashMap.js
  function expandToHashMap(value, keys) {
    return keys.reduce(function(hashMap, key) {
      hashMap[key] = value;
      return hashMap;
    }, {});
  }

  // node_modules/@popperjs/core/lib/modifiers/arrow.js
  var toPaddingObject = function toPaddingObject2(padding, state) {
    padding = typeof padding === "function" ? padding(Object.assign({}, state.rects, {
      placement: state.placement
    })) : padding;
    return mergePaddingObject(typeof padding !== "number" ? padding : expandToHashMap(padding, basePlacements));
  };
  function arrow(_ref) {
    var _state$modifiersData$;
    var state = _ref.state, name = _ref.name, options = _ref.options;
    var arrowElement = state.elements.arrow;
    var popperOffsets2 = state.modifiersData.popperOffsets;
    var basePlacement = getBasePlacement(state.placement);
    var axis = getMainAxisFromPlacement(basePlacement);
    var isVertical = [left, right].indexOf(basePlacement) >= 0;
    var len = isVertical ? "height" : "width";
    if (!arrowElement || !popperOffsets2) {
      return;
    }
    var paddingObject = toPaddingObject(options.padding, state);
    var arrowRect = getLayoutRect(arrowElement);
    var minProp = axis === "y" ? top : left;
    var maxProp = axis === "y" ? bottom : right;
    var endDiff = state.rects.reference[len] + state.rects.reference[axis] - popperOffsets2[axis] - state.rects.popper[len];
    var startDiff = popperOffsets2[axis] - state.rects.reference[axis];
    var arrowOffsetParent = getOffsetParent(arrowElement);
    var clientSize = arrowOffsetParent ? axis === "y" ? arrowOffsetParent.clientHeight || 0 : arrowOffsetParent.clientWidth || 0 : 0;
    var centerToReference = endDiff / 2 - startDiff / 2;
    var min2 = paddingObject[minProp];
    var max2 = clientSize - arrowRect[len] - paddingObject[maxProp];
    var center = clientSize / 2 - arrowRect[len] / 2 + centerToReference;
    var offset2 = within(min2, center, max2);
    var axisProp = axis;
    state.modifiersData[name] = (_state$modifiersData$ = {}, _state$modifiersData$[axisProp] = offset2, _state$modifiersData$.centerOffset = offset2 - center, _state$modifiersData$);
  }
  function effect4(_ref2) {
    var state = _ref2.state, options = _ref2.options;
    var _options$element = options.element, arrowElement = _options$element === void 0 ? "[data-popper-arrow]" : _options$element;
    if (arrowElement == null) {
      return;
    }
    if (typeof arrowElement === "string") {
      arrowElement = state.elements.popper.querySelector(arrowElement);
      if (!arrowElement) {
        return;
      }
    }
    if (!contains(state.elements.popper, arrowElement)) {
      return;
    }
    state.elements.arrow = arrowElement;
  }
  var arrow_default = {
    name: "arrow",
    enabled: true,
    phase: "main",
    fn: arrow,
    effect: effect4,
    requires: ["popperOffsets"],
    requiresIfExists: ["preventOverflow"]
  };

  // node_modules/@popperjs/core/lib/utils/getVariation.js
  function getVariation(placement) {
    return placement.split("-")[1];
  }

  // node_modules/@popperjs/core/lib/modifiers/computeStyles.js
  var unsetSides = {
    top: "auto",
    right: "auto",
    bottom: "auto",
    left: "auto"
  };
  function roundOffsetsByDPR(_ref, win) {
    var x = _ref.x, y = _ref.y;
    var dpr = win.devicePixelRatio || 1;
    return {
      x: round(x * dpr) / dpr || 0,
      y: round(y * dpr) / dpr || 0
    };
  }
  function mapToStyles(_ref2) {
    var _Object$assign2;
    var popper2 = _ref2.popper, popperRect = _ref2.popperRect, placement = _ref2.placement, variation = _ref2.variation, offsets = _ref2.offsets, position = _ref2.position, gpuAcceleration = _ref2.gpuAcceleration, adaptive = _ref2.adaptive, roundOffsets = _ref2.roundOffsets, isFixed = _ref2.isFixed;
    var _offsets$x = offsets.x, x = _offsets$x === void 0 ? 0 : _offsets$x, _offsets$y = offsets.y, y = _offsets$y === void 0 ? 0 : _offsets$y;
    var _ref3 = typeof roundOffsets === "function" ? roundOffsets({
      x,
      y
    }) : {
      x,
      y
    };
    x = _ref3.x;
    y = _ref3.y;
    var hasX = offsets.hasOwnProperty("x");
    var hasY = offsets.hasOwnProperty("y");
    var sideX = left;
    var sideY = top;
    var win = window;
    if (adaptive) {
      var offsetParent = getOffsetParent(popper2);
      var heightProp = "clientHeight";
      var widthProp = "clientWidth";
      if (offsetParent === getWindow(popper2)) {
        offsetParent = getDocumentElement(popper2);
        if (getComputedStyle(offsetParent).position !== "static" && position === "absolute") {
          heightProp = "scrollHeight";
          widthProp = "scrollWidth";
        }
      }
      offsetParent = offsetParent;
      if (placement === top || (placement === left || placement === right) && variation === end) {
        sideY = bottom;
        var offsetY = isFixed && offsetParent === win && win.visualViewport ? win.visualViewport.height : offsetParent[heightProp];
        y -= offsetY - popperRect.height;
        y *= gpuAcceleration ? 1 : -1;
      }
      if (placement === left || (placement === top || placement === bottom) && variation === end) {
        sideX = right;
        var offsetX = isFixed && offsetParent === win && win.visualViewport ? win.visualViewport.width : offsetParent[widthProp];
        x -= offsetX - popperRect.width;
        x *= gpuAcceleration ? 1 : -1;
      }
    }
    var commonStyles = Object.assign({
      position
    }, adaptive && unsetSides);
    var _ref4 = roundOffsets === true ? roundOffsetsByDPR({
      x,
      y
    }, getWindow(popper2)) : {
      x,
      y
    };
    x = _ref4.x;
    y = _ref4.y;
    if (gpuAcceleration) {
      var _Object$assign;
      return Object.assign({}, commonStyles, (_Object$assign = {}, _Object$assign[sideY] = hasY ? "0" : "", _Object$assign[sideX] = hasX ? "0" : "", _Object$assign.transform = (win.devicePixelRatio || 1) <= 1 ? "translate(" + x + "px, " + y + "px)" : "translate3d(" + x + "px, " + y + "px, 0)", _Object$assign));
    }
    return Object.assign({}, commonStyles, (_Object$assign2 = {}, _Object$assign2[sideY] = hasY ? y + "px" : "", _Object$assign2[sideX] = hasX ? x + "px" : "", _Object$assign2.transform = "", _Object$assign2));
  }
  function computeStyles(_ref5) {
    var state = _ref5.state, options = _ref5.options;
    var _options$gpuAccelerat = options.gpuAcceleration, gpuAcceleration = _options$gpuAccelerat === void 0 ? true : _options$gpuAccelerat, _options$adaptive = options.adaptive, adaptive = _options$adaptive === void 0 ? true : _options$adaptive, _options$roundOffsets = options.roundOffsets, roundOffsets = _options$roundOffsets === void 0 ? true : _options$roundOffsets;
    var commonStyles = {
      placement: getBasePlacement(state.placement),
      variation: getVariation(state.placement),
      popper: state.elements.popper,
      popperRect: state.rects.popper,
      gpuAcceleration,
      isFixed: state.options.strategy === "fixed"
    };
    if (state.modifiersData.popperOffsets != null) {
      state.styles.popper = Object.assign({}, state.styles.popper, mapToStyles(Object.assign({}, commonStyles, {
        offsets: state.modifiersData.popperOffsets,
        position: state.options.strategy,
        adaptive,
        roundOffsets
      })));
    }
    if (state.modifiersData.arrow != null) {
      state.styles.arrow = Object.assign({}, state.styles.arrow, mapToStyles(Object.assign({}, commonStyles, {
        offsets: state.modifiersData.arrow,
        position: "absolute",
        adaptive: false,
        roundOffsets
      })));
    }
    state.attributes.popper = Object.assign({}, state.attributes.popper, {
      "data-popper-placement": state.placement
    });
  }
  var computeStyles_default = {
    name: "computeStyles",
    enabled: true,
    phase: "beforeWrite",
    fn: computeStyles,
    data: {}
  };

  // node_modules/@popperjs/core/lib/modifiers/eventListeners.js
  var passive = {
    passive: true
  };
  function effect5(_ref) {
    var state = _ref.state, instance = _ref.instance, options = _ref.options;
    var _options$scroll = options.scroll, scroll = _options$scroll === void 0 ? true : _options$scroll, _options$resize = options.resize, resize = _options$resize === void 0 ? true : _options$resize;
    var window2 = getWindow(state.elements.popper);
    var scrollParents = [].concat(state.scrollParents.reference, state.scrollParents.popper);
    if (scroll) {
      scrollParents.forEach(function(scrollParent) {
        scrollParent.addEventListener("scroll", instance.update, passive);
      });
    }
    if (resize) {
      window2.addEventListener("resize", instance.update, passive);
    }
    return function() {
      if (scroll) {
        scrollParents.forEach(function(scrollParent) {
          scrollParent.removeEventListener("scroll", instance.update, passive);
        });
      }
      if (resize) {
        window2.removeEventListener("resize", instance.update, passive);
      }
    };
  }
  var eventListeners_default = {
    name: "eventListeners",
    enabled: true,
    phase: "write",
    fn: function fn() {
    },
    effect: effect5,
    data: {}
  };

  // node_modules/@popperjs/core/lib/utils/getOppositePlacement.js
  var hash = {
    left: "right",
    right: "left",
    bottom: "top",
    top: "bottom"
  };
  function getOppositePlacement(placement) {
    return placement.replace(/left|right|bottom|top/g, function(matched) {
      return hash[matched];
    });
  }

  // node_modules/@popperjs/core/lib/utils/getOppositeVariationPlacement.js
  var hash2 = {
    start: "end",
    end: "start"
  };
  function getOppositeVariationPlacement(placement) {
    return placement.replace(/start|end/g, function(matched) {
      return hash2[matched];
    });
  }

  // node_modules/@popperjs/core/lib/dom-utils/getWindowScroll.js
  function getWindowScroll(node) {
    var win = getWindow(node);
    var scrollLeft = win.pageXOffset;
    var scrollTop = win.pageYOffset;
    return {
      scrollLeft,
      scrollTop
    };
  }

  // node_modules/@popperjs/core/lib/dom-utils/getWindowScrollBarX.js
  function getWindowScrollBarX(element) {
    return getBoundingClientRect(getDocumentElement(element)).left + getWindowScroll(element).scrollLeft;
  }

  // node_modules/@popperjs/core/lib/dom-utils/getViewportRect.js
  function getViewportRect(element, strategy) {
    var win = getWindow(element);
    var html = getDocumentElement(element);
    var visualViewport = win.visualViewport;
    var width = html.clientWidth;
    var height = html.clientHeight;
    var x = 0;
    var y = 0;
    if (visualViewport) {
      width = visualViewport.width;
      height = visualViewport.height;
      var layoutViewport = isLayoutViewport();
      if (layoutViewport || !layoutViewport && strategy === "fixed") {
        x = visualViewport.offsetLeft;
        y = visualViewport.offsetTop;
      }
    }
    return {
      width,
      height,
      x: x + getWindowScrollBarX(element),
      y
    };
  }

  // node_modules/@popperjs/core/lib/dom-utils/getDocumentRect.js
  function getDocumentRect(element) {
    var _element$ownerDocumen;
    var html = getDocumentElement(element);
    var winScroll = getWindowScroll(element);
    var body = (_element$ownerDocumen = element.ownerDocument) == null ? void 0 : _element$ownerDocumen.body;
    var width = max(html.scrollWidth, html.clientWidth, body ? body.scrollWidth : 0, body ? body.clientWidth : 0);
    var height = max(html.scrollHeight, html.clientHeight, body ? body.scrollHeight : 0, body ? body.clientHeight : 0);
    var x = -winScroll.scrollLeft + getWindowScrollBarX(element);
    var y = -winScroll.scrollTop;
    if (getComputedStyle(body || html).direction === "rtl") {
      x += max(html.clientWidth, body ? body.clientWidth : 0) - width;
    }
    return {
      width,
      height,
      x,
      y
    };
  }

  // node_modules/@popperjs/core/lib/dom-utils/isScrollParent.js
  function isScrollParent(element) {
    var _getComputedStyle = getComputedStyle(element), overflow = _getComputedStyle.overflow, overflowX = _getComputedStyle.overflowX, overflowY = _getComputedStyle.overflowY;
    return /auto|scroll|overlay|hidden/.test(overflow + overflowY + overflowX);
  }

  // node_modules/@popperjs/core/lib/dom-utils/getScrollParent.js
  function getScrollParent(node) {
    if (["html", "body", "#document"].indexOf(getNodeName(node)) >= 0) {
      return node.ownerDocument.body;
    }
    if (isHTMLElement(node) && isScrollParent(node)) {
      return node;
    }
    return getScrollParent(getParentNode(node));
  }

  // node_modules/@popperjs/core/lib/dom-utils/listScrollParents.js
  function listScrollParents(element, list) {
    var _element$ownerDocumen;
    if (list === void 0) {
      list = [];
    }
    var scrollParent = getScrollParent(element);
    var isBody = scrollParent === ((_element$ownerDocumen = element.ownerDocument) == null ? void 0 : _element$ownerDocumen.body);
    var win = getWindow(scrollParent);
    var target = isBody ? [win].concat(win.visualViewport || [], isScrollParent(scrollParent) ? scrollParent : []) : scrollParent;
    var updatedList = list.concat(target);
    return isBody ? updatedList : updatedList.concat(listScrollParents(getParentNode(target)));
  }

  // node_modules/@popperjs/core/lib/utils/rectToClientRect.js
  function rectToClientRect(rect) {
    return Object.assign({}, rect, {
      left: rect.x,
      top: rect.y,
      right: rect.x + rect.width,
      bottom: rect.y + rect.height
    });
  }

  // node_modules/@popperjs/core/lib/dom-utils/getClippingRect.js
  function getInnerBoundingClientRect(element, strategy) {
    var rect = getBoundingClientRect(element, false, strategy === "fixed");
    rect.top = rect.top + element.clientTop;
    rect.left = rect.left + element.clientLeft;
    rect.bottom = rect.top + element.clientHeight;
    rect.right = rect.left + element.clientWidth;
    rect.width = element.clientWidth;
    rect.height = element.clientHeight;
    rect.x = rect.left;
    rect.y = rect.top;
    return rect;
  }
  function getClientRectFromMixedType(element, clippingParent, strategy) {
    return clippingParent === viewport ? rectToClientRect(getViewportRect(element, strategy)) : isElement(clippingParent) ? getInnerBoundingClientRect(clippingParent, strategy) : rectToClientRect(getDocumentRect(getDocumentElement(element)));
  }
  function getClippingParents(element) {
    var clippingParents2 = listScrollParents(getParentNode(element));
    var canEscapeClipping = ["absolute", "fixed"].indexOf(getComputedStyle(element).position) >= 0;
    var clipperElement = canEscapeClipping && isHTMLElement(element) ? getOffsetParent(element) : element;
    if (!isElement(clipperElement)) {
      return [];
    }
    return clippingParents2.filter(function(clippingParent) {
      return isElement(clippingParent) && contains(clippingParent, clipperElement) && getNodeName(clippingParent) !== "body";
    });
  }
  function getClippingRect(element, boundary, rootBoundary, strategy) {
    var mainClippingParents = boundary === "clippingParents" ? getClippingParents(element) : [].concat(boundary);
    var clippingParents2 = [].concat(mainClippingParents, [rootBoundary]);
    var firstClippingParent = clippingParents2[0];
    var clippingRect = clippingParents2.reduce(function(accRect, clippingParent) {
      var rect = getClientRectFromMixedType(element, clippingParent, strategy);
      accRect.top = max(rect.top, accRect.top);
      accRect.right = min(rect.right, accRect.right);
      accRect.bottom = min(rect.bottom, accRect.bottom);
      accRect.left = max(rect.left, accRect.left);
      return accRect;
    }, getClientRectFromMixedType(element, firstClippingParent, strategy));
    clippingRect.width = clippingRect.right - clippingRect.left;
    clippingRect.height = clippingRect.bottom - clippingRect.top;
    clippingRect.x = clippingRect.left;
    clippingRect.y = clippingRect.top;
    return clippingRect;
  }

  // node_modules/@popperjs/core/lib/utils/computeOffsets.js
  function computeOffsets(_ref) {
    var reference2 = _ref.reference, element = _ref.element, placement = _ref.placement;
    var basePlacement = placement ? getBasePlacement(placement) : null;
    var variation = placement ? getVariation(placement) : null;
    var commonX = reference2.x + reference2.width / 2 - element.width / 2;
    var commonY = reference2.y + reference2.height / 2 - element.height / 2;
    var offsets;
    switch (basePlacement) {
      case top:
        offsets = {
          x: commonX,
          y: reference2.y - element.height
        };
        break;
      case bottom:
        offsets = {
          x: commonX,
          y: reference2.y + reference2.height
        };
        break;
      case right:
        offsets = {
          x: reference2.x + reference2.width,
          y: commonY
        };
        break;
      case left:
        offsets = {
          x: reference2.x - element.width,
          y: commonY
        };
        break;
      default:
        offsets = {
          x: reference2.x,
          y: reference2.y
        };
    }
    var mainAxis = basePlacement ? getMainAxisFromPlacement(basePlacement) : null;
    if (mainAxis != null) {
      var len = mainAxis === "y" ? "height" : "width";
      switch (variation) {
        case start:
          offsets[mainAxis] = offsets[mainAxis] - (reference2[len] / 2 - element[len] / 2);
          break;
        case end:
          offsets[mainAxis] = offsets[mainAxis] + (reference2[len] / 2 - element[len] / 2);
          break;
        default:
      }
    }
    return offsets;
  }

  // node_modules/@popperjs/core/lib/utils/detectOverflow.js
  function detectOverflow(state, options) {
    if (options === void 0) {
      options = {};
    }
    var _options = options, _options$placement = _options.placement, placement = _options$placement === void 0 ? state.placement : _options$placement, _options$strategy = _options.strategy, strategy = _options$strategy === void 0 ? state.strategy : _options$strategy, _options$boundary = _options.boundary, boundary = _options$boundary === void 0 ? clippingParents : _options$boundary, _options$rootBoundary = _options.rootBoundary, rootBoundary = _options$rootBoundary === void 0 ? viewport : _options$rootBoundary, _options$elementConte = _options.elementContext, elementContext = _options$elementConte === void 0 ? popper : _options$elementConte, _options$altBoundary = _options.altBoundary, altBoundary = _options$altBoundary === void 0 ? false : _options$altBoundary, _options$padding = _options.padding, padding = _options$padding === void 0 ? 0 : _options$padding;
    var paddingObject = mergePaddingObject(typeof padding !== "number" ? padding : expandToHashMap(padding, basePlacements));
    var altContext = elementContext === popper ? reference : popper;
    var popperRect = state.rects.popper;
    var element = state.elements[altBoundary ? altContext : elementContext];
    var clippingClientRect = getClippingRect(isElement(element) ? element : element.contextElement || getDocumentElement(state.elements.popper), boundary, rootBoundary, strategy);
    var referenceClientRect = getBoundingClientRect(state.elements.reference);
    var popperOffsets2 = computeOffsets({
      reference: referenceClientRect,
      element: popperRect,
      strategy: "absolute",
      placement
    });
    var popperClientRect = rectToClientRect(Object.assign({}, popperRect, popperOffsets2));
    var elementClientRect = elementContext === popper ? popperClientRect : referenceClientRect;
    var overflowOffsets = {
      top: clippingClientRect.top - elementClientRect.top + paddingObject.top,
      bottom: elementClientRect.bottom - clippingClientRect.bottom + paddingObject.bottom,
      left: clippingClientRect.left - elementClientRect.left + paddingObject.left,
      right: elementClientRect.right - clippingClientRect.right + paddingObject.right
    };
    var offsetData = state.modifiersData.offset;
    if (elementContext === popper && offsetData) {
      var offset2 = offsetData[placement];
      Object.keys(overflowOffsets).forEach(function(key) {
        var multiply = [right, bottom].indexOf(key) >= 0 ? 1 : -1;
        var axis = [top, bottom].indexOf(key) >= 0 ? "y" : "x";
        overflowOffsets[key] += offset2[axis] * multiply;
      });
    }
    return overflowOffsets;
  }

  // node_modules/@popperjs/core/lib/utils/computeAutoPlacement.js
  function computeAutoPlacement(state, options) {
    if (options === void 0) {
      options = {};
    }
    var _options = options, placement = _options.placement, boundary = _options.boundary, rootBoundary = _options.rootBoundary, padding = _options.padding, flipVariations = _options.flipVariations, _options$allowedAutoP = _options.allowedAutoPlacements, allowedAutoPlacements = _options$allowedAutoP === void 0 ? placements : _options$allowedAutoP;
    var variation = getVariation(placement);
    var placements2 = variation ? flipVariations ? variationPlacements : variationPlacements.filter(function(placement2) {
      return getVariation(placement2) === variation;
    }) : basePlacements;
    var allowedPlacements = placements2.filter(function(placement2) {
      return allowedAutoPlacements.indexOf(placement2) >= 0;
    });
    if (allowedPlacements.length === 0) {
      allowedPlacements = placements2;
    }
    var overflows = allowedPlacements.reduce(function(acc, placement2) {
      acc[placement2] = detectOverflow(state, {
        placement: placement2,
        boundary,
        rootBoundary,
        padding
      })[getBasePlacement(placement2)];
      return acc;
    }, {});
    return Object.keys(overflows).sort(function(a, b) {
      return overflows[a] - overflows[b];
    });
  }

  // node_modules/@popperjs/core/lib/modifiers/flip.js
  function getExpandedFallbackPlacements(placement) {
    if (getBasePlacement(placement) === auto) {
      return [];
    }
    var oppositePlacement = getOppositePlacement(placement);
    return [getOppositeVariationPlacement(placement), oppositePlacement, getOppositeVariationPlacement(oppositePlacement)];
  }
  function flip(_ref) {
    var state = _ref.state, options = _ref.options, name = _ref.name;
    if (state.modifiersData[name]._skip) {
      return;
    }
    var _options$mainAxis = options.mainAxis, checkMainAxis = _options$mainAxis === void 0 ? true : _options$mainAxis, _options$altAxis = options.altAxis, checkAltAxis = _options$altAxis === void 0 ? true : _options$altAxis, specifiedFallbackPlacements = options.fallbackPlacements, padding = options.padding, boundary = options.boundary, rootBoundary = options.rootBoundary, altBoundary = options.altBoundary, _options$flipVariatio = options.flipVariations, flipVariations = _options$flipVariatio === void 0 ? true : _options$flipVariatio, allowedAutoPlacements = options.allowedAutoPlacements;
    var preferredPlacement = state.options.placement;
    var basePlacement = getBasePlacement(preferredPlacement);
    var isBasePlacement = basePlacement === preferredPlacement;
    var fallbackPlacements = specifiedFallbackPlacements || (isBasePlacement || !flipVariations ? [getOppositePlacement(preferredPlacement)] : getExpandedFallbackPlacements(preferredPlacement));
    var placements2 = [preferredPlacement].concat(fallbackPlacements).reduce(function(acc, placement2) {
      return acc.concat(getBasePlacement(placement2) === auto ? computeAutoPlacement(state, {
        placement: placement2,
        boundary,
        rootBoundary,
        padding,
        flipVariations,
        allowedAutoPlacements
      }) : placement2);
    }, []);
    var referenceRect = state.rects.reference;
    var popperRect = state.rects.popper;
    var checksMap = /* @__PURE__ */ new Map();
    var makeFallbackChecks = true;
    var firstFittingPlacement = placements2[0];
    for (var i = 0; i < placements2.length; i++) {
      var placement = placements2[i];
      var _basePlacement = getBasePlacement(placement);
      var isStartVariation = getVariation(placement) === start;
      var isVertical = [top, bottom].indexOf(_basePlacement) >= 0;
      var len = isVertical ? "width" : "height";
      var overflow = detectOverflow(state, {
        placement,
        boundary,
        rootBoundary,
        altBoundary,
        padding
      });
      var mainVariationSide = isVertical ? isStartVariation ? right : left : isStartVariation ? bottom : top;
      if (referenceRect[len] > popperRect[len]) {
        mainVariationSide = getOppositePlacement(mainVariationSide);
      }
      var altVariationSide = getOppositePlacement(mainVariationSide);
      var checks = [];
      if (checkMainAxis) {
        checks.push(overflow[_basePlacement] <= 0);
      }
      if (checkAltAxis) {
        checks.push(overflow[mainVariationSide] <= 0, overflow[altVariationSide] <= 0);
      }
      if (checks.every(function(check) {
        return check;
      })) {
        firstFittingPlacement = placement;
        makeFallbackChecks = false;
        break;
      }
      checksMap.set(placement, checks);
    }
    if (makeFallbackChecks) {
      var numberOfChecks = flipVariations ? 3 : 1;
      var _loop = function _loop2(_i2) {
        var fittingPlacement = placements2.find(function(placement2) {
          var checks2 = checksMap.get(placement2);
          if (checks2) {
            return checks2.slice(0, _i2).every(function(check) {
              return check;
            });
          }
        });
        if (fittingPlacement) {
          firstFittingPlacement = fittingPlacement;
          return "break";
        }
      };
      for (var _i = numberOfChecks; _i > 0; _i--) {
        var _ret = _loop(_i);
        if (_ret === "break")
          break;
      }
    }
    if (state.placement !== firstFittingPlacement) {
      state.modifiersData[name]._skip = true;
      state.placement = firstFittingPlacement;
      state.reset = true;
    }
  }
  var flip_default = {
    name: "flip",
    enabled: true,
    phase: "main",
    fn: flip,
    requiresIfExists: ["offset"],
    data: {
      _skip: false
    }
  };

  // node_modules/@popperjs/core/lib/modifiers/hide.js
  function getSideOffsets(overflow, rect, preventedOffsets) {
    if (preventedOffsets === void 0) {
      preventedOffsets = {
        x: 0,
        y: 0
      };
    }
    return {
      top: overflow.top - rect.height - preventedOffsets.y,
      right: overflow.right - rect.width + preventedOffsets.x,
      bottom: overflow.bottom - rect.height + preventedOffsets.y,
      left: overflow.left - rect.width - preventedOffsets.x
    };
  }
  function isAnySideFullyClipped(overflow) {
    return [top, right, bottom, left].some(function(side) {
      return overflow[side] >= 0;
    });
  }
  function hide(_ref) {
    var state = _ref.state, name = _ref.name;
    var referenceRect = state.rects.reference;
    var popperRect = state.rects.popper;
    var preventedOffsets = state.modifiersData.preventOverflow;
    var referenceOverflow = detectOverflow(state, {
      elementContext: "reference"
    });
    var popperAltOverflow = detectOverflow(state, {
      altBoundary: true
    });
    var referenceClippingOffsets = getSideOffsets(referenceOverflow, referenceRect);
    var popperEscapeOffsets = getSideOffsets(popperAltOverflow, popperRect, preventedOffsets);
    var isReferenceHidden = isAnySideFullyClipped(referenceClippingOffsets);
    var hasPopperEscaped = isAnySideFullyClipped(popperEscapeOffsets);
    state.modifiersData[name] = {
      referenceClippingOffsets,
      popperEscapeOffsets,
      isReferenceHidden,
      hasPopperEscaped
    };
    state.attributes.popper = Object.assign({}, state.attributes.popper, {
      "data-popper-reference-hidden": isReferenceHidden,
      "data-popper-escaped": hasPopperEscaped
    });
  }
  var hide_default = {
    name: "hide",
    enabled: true,
    phase: "main",
    requiresIfExists: ["preventOverflow"],
    fn: hide
  };

  // node_modules/@popperjs/core/lib/modifiers/offset.js
  function distanceAndSkiddingToXY(placement, rects, offset2) {
    var basePlacement = getBasePlacement(placement);
    var invertDistance = [left, top].indexOf(basePlacement) >= 0 ? -1 : 1;
    var _ref = typeof offset2 === "function" ? offset2(Object.assign({}, rects, {
      placement
    })) : offset2, skidding = _ref[0], distance = _ref[1];
    skidding = skidding || 0;
    distance = (distance || 0) * invertDistance;
    return [left, right].indexOf(basePlacement) >= 0 ? {
      x: distance,
      y: skidding
    } : {
      x: skidding,
      y: distance
    };
  }
  function offset(_ref2) {
    var state = _ref2.state, options = _ref2.options, name = _ref2.name;
    var _options$offset = options.offset, offset2 = _options$offset === void 0 ? [0, 0] : _options$offset;
    var data = placements.reduce(function(acc, placement) {
      acc[placement] = distanceAndSkiddingToXY(placement, state.rects, offset2);
      return acc;
    }, {});
    var _data$state$placement = data[state.placement], x = _data$state$placement.x, y = _data$state$placement.y;
    if (state.modifiersData.popperOffsets != null) {
      state.modifiersData.popperOffsets.x += x;
      state.modifiersData.popperOffsets.y += y;
    }
    state.modifiersData[name] = data;
  }
  var offset_default = {
    name: "offset",
    enabled: true,
    phase: "main",
    requires: ["popperOffsets"],
    fn: offset
  };

  // node_modules/@popperjs/core/lib/modifiers/popperOffsets.js
  function popperOffsets(_ref) {
    var state = _ref.state, name = _ref.name;
    state.modifiersData[name] = computeOffsets({
      reference: state.rects.reference,
      element: state.rects.popper,
      strategy: "absolute",
      placement: state.placement
    });
  }
  var popperOffsets_default = {
    name: "popperOffsets",
    enabled: true,
    phase: "read",
    fn: popperOffsets,
    data: {}
  };

  // node_modules/@popperjs/core/lib/utils/getAltAxis.js
  function getAltAxis(axis) {
    return axis === "x" ? "y" : "x";
  }

  // node_modules/@popperjs/core/lib/modifiers/preventOverflow.js
  function preventOverflow(_ref) {
    var state = _ref.state, options = _ref.options, name = _ref.name;
    var _options$mainAxis = options.mainAxis, checkMainAxis = _options$mainAxis === void 0 ? true : _options$mainAxis, _options$altAxis = options.altAxis, checkAltAxis = _options$altAxis === void 0 ? false : _options$altAxis, boundary = options.boundary, rootBoundary = options.rootBoundary, altBoundary = options.altBoundary, padding = options.padding, _options$tether = options.tether, tether = _options$tether === void 0 ? true : _options$tether, _options$tetherOffset = options.tetherOffset, tetherOffset = _options$tetherOffset === void 0 ? 0 : _options$tetherOffset;
    var overflow = detectOverflow(state, {
      boundary,
      rootBoundary,
      padding,
      altBoundary
    });
    var basePlacement = getBasePlacement(state.placement);
    var variation = getVariation(state.placement);
    var isBasePlacement = !variation;
    var mainAxis = getMainAxisFromPlacement(basePlacement);
    var altAxis = getAltAxis(mainAxis);
    var popperOffsets2 = state.modifiersData.popperOffsets;
    var referenceRect = state.rects.reference;
    var popperRect = state.rects.popper;
    var tetherOffsetValue = typeof tetherOffset === "function" ? tetherOffset(Object.assign({}, state.rects, {
      placement: state.placement
    })) : tetherOffset;
    var normalizedTetherOffsetValue = typeof tetherOffsetValue === "number" ? {
      mainAxis: tetherOffsetValue,
      altAxis: tetherOffsetValue
    } : Object.assign({
      mainAxis: 0,
      altAxis: 0
    }, tetherOffsetValue);
    var offsetModifierState = state.modifiersData.offset ? state.modifiersData.offset[state.placement] : null;
    var data = {
      x: 0,
      y: 0
    };
    if (!popperOffsets2) {
      return;
    }
    if (checkMainAxis) {
      var _offsetModifierState$;
      var mainSide = mainAxis === "y" ? top : left;
      var altSide = mainAxis === "y" ? bottom : right;
      var len = mainAxis === "y" ? "height" : "width";
      var offset2 = popperOffsets2[mainAxis];
      var min2 = offset2 + overflow[mainSide];
      var max2 = offset2 - overflow[altSide];
      var additive = tether ? -popperRect[len] / 2 : 0;
      var minLen = variation === start ? referenceRect[len] : popperRect[len];
      var maxLen = variation === start ? -popperRect[len] : -referenceRect[len];
      var arrowElement = state.elements.arrow;
      var arrowRect = tether && arrowElement ? getLayoutRect(arrowElement) : {
        width: 0,
        height: 0
      };
      var arrowPaddingObject = state.modifiersData["arrow#persistent"] ? state.modifiersData["arrow#persistent"].padding : getFreshSideObject();
      var arrowPaddingMin = arrowPaddingObject[mainSide];
      var arrowPaddingMax = arrowPaddingObject[altSide];
      var arrowLen = within(0, referenceRect[len], arrowRect[len]);
      var minOffset = isBasePlacement ? referenceRect[len] / 2 - additive - arrowLen - arrowPaddingMin - normalizedTetherOffsetValue.mainAxis : minLen - arrowLen - arrowPaddingMin - normalizedTetherOffsetValue.mainAxis;
      var maxOffset = isBasePlacement ? -referenceRect[len] / 2 + additive + arrowLen + arrowPaddingMax + normalizedTetherOffsetValue.mainAxis : maxLen + arrowLen + arrowPaddingMax + normalizedTetherOffsetValue.mainAxis;
      var arrowOffsetParent = state.elements.arrow && getOffsetParent(state.elements.arrow);
      var clientOffset = arrowOffsetParent ? mainAxis === "y" ? arrowOffsetParent.clientTop || 0 : arrowOffsetParent.clientLeft || 0 : 0;
      var offsetModifierValue = (_offsetModifierState$ = offsetModifierState == null ? void 0 : offsetModifierState[mainAxis]) != null ? _offsetModifierState$ : 0;
      var tetherMin = offset2 + minOffset - offsetModifierValue - clientOffset;
      var tetherMax = offset2 + maxOffset - offsetModifierValue;
      var preventedOffset = within(tether ? min(min2, tetherMin) : min2, offset2, tether ? max(max2, tetherMax) : max2);
      popperOffsets2[mainAxis] = preventedOffset;
      data[mainAxis] = preventedOffset - offset2;
    }
    if (checkAltAxis) {
      var _offsetModifierState$2;
      var _mainSide = mainAxis === "x" ? top : left;
      var _altSide = mainAxis === "x" ? bottom : right;
      var _offset = popperOffsets2[altAxis];
      var _len = altAxis === "y" ? "height" : "width";
      var _min = _offset + overflow[_mainSide];
      var _max = _offset - overflow[_altSide];
      var isOriginSide = [top, left].indexOf(basePlacement) !== -1;
      var _offsetModifierValue = (_offsetModifierState$2 = offsetModifierState == null ? void 0 : offsetModifierState[altAxis]) != null ? _offsetModifierState$2 : 0;
      var _tetherMin = isOriginSide ? _min : _offset - referenceRect[_len] - popperRect[_len] - _offsetModifierValue + normalizedTetherOffsetValue.altAxis;
      var _tetherMax = isOriginSide ? _offset + referenceRect[_len] + popperRect[_len] - _offsetModifierValue - normalizedTetherOffsetValue.altAxis : _max;
      var _preventedOffset = tether && isOriginSide ? withinMaxClamp(_tetherMin, _offset, _tetherMax) : within(tether ? _tetherMin : _min, _offset, tether ? _tetherMax : _max);
      popperOffsets2[altAxis] = _preventedOffset;
      data[altAxis] = _preventedOffset - _offset;
    }
    state.modifiersData[name] = data;
  }
  var preventOverflow_default = {
    name: "preventOverflow",
    enabled: true,
    phase: "main",
    fn: preventOverflow,
    requiresIfExists: ["offset"]
  };

  // node_modules/@popperjs/core/lib/dom-utils/getHTMLElementScroll.js
  function getHTMLElementScroll(element) {
    return {
      scrollLeft: element.scrollLeft,
      scrollTop: element.scrollTop
    };
  }

  // node_modules/@popperjs/core/lib/dom-utils/getNodeScroll.js
  function getNodeScroll(node) {
    if (node === getWindow(node) || !isHTMLElement(node)) {
      return getWindowScroll(node);
    } else {
      return getHTMLElementScroll(node);
    }
  }

  // node_modules/@popperjs/core/lib/dom-utils/getCompositeRect.js
  function isElementScaled(element) {
    var rect = element.getBoundingClientRect();
    var scaleX = round(rect.width) / element.offsetWidth || 1;
    var scaleY = round(rect.height) / element.offsetHeight || 1;
    return scaleX !== 1 || scaleY !== 1;
  }
  function getCompositeRect(elementOrVirtualElement, offsetParent, isFixed) {
    if (isFixed === void 0) {
      isFixed = false;
    }
    var isOffsetParentAnElement = isHTMLElement(offsetParent);
    var offsetParentIsScaled = isHTMLElement(offsetParent) && isElementScaled(offsetParent);
    var documentElement = getDocumentElement(offsetParent);
    var rect = getBoundingClientRect(elementOrVirtualElement, offsetParentIsScaled, isFixed);
    var scroll = {
      scrollLeft: 0,
      scrollTop: 0
    };
    var offsets = {
      x: 0,
      y: 0
    };
    if (isOffsetParentAnElement || !isOffsetParentAnElement && !isFixed) {
      if (getNodeName(offsetParent) !== "body" || isScrollParent(documentElement)) {
        scroll = getNodeScroll(offsetParent);
      }
      if (isHTMLElement(offsetParent)) {
        offsets = getBoundingClientRect(offsetParent, true);
        offsets.x += offsetParent.clientLeft;
        offsets.y += offsetParent.clientTop;
      } else if (documentElement) {
        offsets.x = getWindowScrollBarX(documentElement);
      }
    }
    return {
      x: rect.left + scroll.scrollLeft - offsets.x,
      y: rect.top + scroll.scrollTop - offsets.y,
      width: rect.width,
      height: rect.height
    };
  }

  // node_modules/@popperjs/core/lib/utils/orderModifiers.js
  function order(modifiers) {
    var map3 = /* @__PURE__ */ new Map();
    var visited = /* @__PURE__ */ new Set();
    var result = [];
    modifiers.forEach(function(modifier) {
      map3.set(modifier.name, modifier);
    });
    function sort(modifier) {
      visited.add(modifier.name);
      var requires = [].concat(modifier.requires || [], modifier.requiresIfExists || []);
      requires.forEach(function(dep) {
        if (!visited.has(dep)) {
          var depModifier = map3.get(dep);
          if (depModifier) {
            sort(depModifier);
          }
        }
      });
      result.push(modifier);
    }
    modifiers.forEach(function(modifier) {
      if (!visited.has(modifier.name)) {
        sort(modifier);
      }
    });
    return result;
  }
  function orderModifiers(modifiers) {
    var orderedModifiers = order(modifiers);
    return modifierPhases.reduce(function(acc, phase) {
      return acc.concat(orderedModifiers.filter(function(modifier) {
        return modifier.phase === phase;
      }));
    }, []);
  }

  // node_modules/@popperjs/core/lib/utils/debounce.js
  function debounce(fn2) {
    var pending;
    return function() {
      if (!pending) {
        pending = new Promise(function(resolve) {
          Promise.resolve().then(function() {
            pending = void 0;
            resolve(fn2());
          });
        });
      }
      return pending;
    };
  }

  // node_modules/@popperjs/core/lib/utils/mergeByName.js
  function mergeByName(modifiers) {
    var merged = modifiers.reduce(function(merged2, current) {
      var existing = merged2[current.name];
      merged2[current.name] = existing ? Object.assign({}, existing, current, {
        options: Object.assign({}, existing.options, current.options),
        data: Object.assign({}, existing.data, current.data)
      }) : current;
      return merged2;
    }, {});
    return Object.keys(merged).map(function(key) {
      return merged[key];
    });
  }

  // node_modules/@popperjs/core/lib/createPopper.js
  var DEFAULT_OPTIONS = {
    placement: "bottom",
    modifiers: [],
    strategy: "absolute"
  };
  function areValidElements() {
    for (var _len = arguments.length, args = new Array(_len), _key = 0; _key < _len; _key++) {
      args[_key] = arguments[_key];
    }
    return !args.some(function(element) {
      return !(element && typeof element.getBoundingClientRect === "function");
    });
  }
  function popperGenerator(generatorOptions) {
    if (generatorOptions === void 0) {
      generatorOptions = {};
    }
    var _generatorOptions = generatorOptions, _generatorOptions$def = _generatorOptions.defaultModifiers, defaultModifiers2 = _generatorOptions$def === void 0 ? [] : _generatorOptions$def, _generatorOptions$def2 = _generatorOptions.defaultOptions, defaultOptions = _generatorOptions$def2 === void 0 ? DEFAULT_OPTIONS : _generatorOptions$def2;
    return function createPopper2(reference2, popper2, options) {
      if (options === void 0) {
        options = defaultOptions;
      }
      var state = {
        placement: "bottom",
        orderedModifiers: [],
        options: Object.assign({}, DEFAULT_OPTIONS, defaultOptions),
        modifiersData: {},
        elements: {
          reference: reference2,
          popper: popper2
        },
        attributes: {},
        styles: {}
      };
      var effectCleanupFns = [];
      var isDestroyed = false;
      var instance = {
        state,
        setOptions: function setOptions(setOptionsAction) {
          var options2 = typeof setOptionsAction === "function" ? setOptionsAction(state.options) : setOptionsAction;
          cleanupModifierEffects();
          state.options = Object.assign({}, defaultOptions, state.options, options2);
          state.scrollParents = {
            reference: isElement(reference2) ? listScrollParents(reference2) : reference2.contextElement ? listScrollParents(reference2.contextElement) : [],
            popper: listScrollParents(popper2)
          };
          var orderedModifiers = orderModifiers(mergeByName([].concat(defaultModifiers2, state.options.modifiers)));
          state.orderedModifiers = orderedModifiers.filter(function(m) {
            return m.enabled;
          });
          runModifierEffects();
          return instance.update();
        },
        forceUpdate: function forceUpdate() {
          if (isDestroyed) {
            return;
          }
          var _state$elements = state.elements, reference3 = _state$elements.reference, popper3 = _state$elements.popper;
          if (!areValidElements(reference3, popper3)) {
            return;
          }
          state.rects = {
            reference: getCompositeRect(reference3, getOffsetParent(popper3), state.options.strategy === "fixed"),
            popper: getLayoutRect(popper3)
          };
          state.reset = false;
          state.placement = state.options.placement;
          state.orderedModifiers.forEach(function(modifier) {
            return state.modifiersData[modifier.name] = Object.assign({}, modifier.data);
          });
          for (var index = 0; index < state.orderedModifiers.length; index++) {
            if (state.reset === true) {
              state.reset = false;
              index = -1;
              continue;
            }
            var _state$orderedModifie = state.orderedModifiers[index], fn2 = _state$orderedModifie.fn, _state$orderedModifie2 = _state$orderedModifie.options, _options = _state$orderedModifie2 === void 0 ? {} : _state$orderedModifie2, name = _state$orderedModifie.name;
            if (typeof fn2 === "function") {
              state = fn2({
                state,
                options: _options,
                name,
                instance
              }) || state;
            }
          }
        },
        update: debounce(function() {
          return new Promise(function(resolve) {
            instance.forceUpdate();
            resolve(state);
          });
        }),
        destroy: function destroy() {
          cleanupModifierEffects();
          isDestroyed = true;
        }
      };
      if (!areValidElements(reference2, popper2)) {
        return instance;
      }
      instance.setOptions(options).then(function(state2) {
        if (!isDestroyed && options.onFirstUpdate) {
          options.onFirstUpdate(state2);
        }
      });
      function runModifierEffects() {
        state.orderedModifiers.forEach(function(_ref) {
          var name = _ref.name, _ref$options = _ref.options, options2 = _ref$options === void 0 ? {} : _ref$options, effect6 = _ref.effect;
          if (typeof effect6 === "function") {
            var cleanupFn = effect6({
              state,
              name,
              instance,
              options: options2
            });
            var noopFn = function noopFn2() {
            };
            effectCleanupFns.push(cleanupFn || noopFn);
          }
        });
      }
      function cleanupModifierEffects() {
        effectCleanupFns.forEach(function(fn2) {
          return fn2();
        });
        effectCleanupFns = [];
      }
      return instance;
    };
  }

  // node_modules/@popperjs/core/lib/popper.js
  var defaultModifiers = [eventListeners_default, popperOffsets_default, computeStyles_default, applyStyles_default, offset_default, flip_default, preventOverflow_default, arrow_default, hide_default];
  var createPopper = /* @__PURE__ */ popperGenerator({
    defaultModifiers
  });

  // sfc-script:/home/frappe/yefri-bench/apps/frappe/frappe/public/js/frappe/file_uploader/TreeNode.vue?type=script
  var TreeNode_default2 = {
    __name: "TreeNode",
    props: {
      node: Object,
      selected_node: Object
    },
    emits: ["node-click", "load-more"],
    setup(__props, { expose: __expose, emit: __emit }) {
      __expose();
      const props = __props;
      let emit2 = __emit;
      let icon = computed4(() => {
        let icons = {
          open: frappe.utils.icon("folder-open", "md"),
          closed: frappe.utils.icon("folder-normal", "md"),
          leaf: frappe.utils.icon("primitive-dot", "xs"),
          search: frappe.utils.icon("search")
        };
        if (props.node.by_search)
          return icons.search;
        if (props.node.is_leaf)
          return icons.leaf;
        if (props.node.open)
          return icons.open;
        return icons.closed;
      });
      let open_file = (filename) => {
        return frappe.utils.get_form_link("File", filename);
      };
      const reference2 = ref2(null);
      const popover = ref2(null);
      let isOpen = ref2(false);
      let popper2 = ref2(null);
      function setupPopper() {
        if (!popper2.value) {
          popper2.value = createPopper(reference2.value, popover.value, {
            placement: "top",
            modifiers: [
              {
                name: "offset",
                options: {
                  offset: [0, 4]
                }
              }
            ]
          });
        } else {
          popper2.value.update();
        }
      }
      let hoverTimer = null;
      let leaveTimer = null;
      function onMouseover() {
        leaveTimer && clearTimeout(leaveTimer) && (leaveTimer = null);
        hoverTimer && clearTimeout(hoverTimer);
        hoverTimer = setTimeout(() => {
          isOpen.value = true;
          setupPopper();
        }, 800);
      }
      function onMouseleave() {
        hoverTimer && clearTimeout(hoverTimer) && (hoverTimer = null);
        leaveTimer && clearTimeout(leaveTimer);
        leaveTimer = setTimeout(() => {
          isOpen.value = false;
        }, 100);
      }
      const __returned__ = { props, get emit() {
        return emit2;
      }, set emit(v) {
        emit2 = v;
      }, get icon() {
        return icon;
      }, set icon(v) {
        icon = v;
      }, get open_file() {
        return open_file;
      }, set open_file(v) {
        open_file = v;
      }, reference: reference2, popover, get isOpen() {
        return isOpen;
      }, set isOpen(v) {
        isOpen = v;
      }, get popper() {
        return popper2;
      }, set popper(v) {
        popper2 = v;
      }, setupPopper, get hoverTimer() {
        return hoverTimer;
      }, set hoverTimer(v) {
        hoverTimer = v;
      }, get leaveTimer() {
        return leaveTimer;
      }, set leaveTimer(v) {
        leaveTimer = v;
      }, onMouseover, onMouseleave, TreeNode: TreeNode_default, get createPopper() {
        return createPopper;
      }, ref: ref2, computed: computed4 };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  };

  // sfc-template:/home/frappe/yefri-bench/apps/frappe/frappe/public/js/frappe/file_uploader/TreeNode.vue?type=template
  var _hoisted_110 = ["disabled"];
  var _hoisted_23 = ["innerHTML"];
  var _hoisted_33 = { class: "tree-label" };
  var _hoisted_43 = ["href", "disabled", "innerHTML"];
  var _hoisted_52 = { key: 0 };
  var _hoisted_62 = {
    class: "popover",
    ref: "popover",
    role: "tooltip"
  };
  var _hoisted_72 = ["src"];
  var _hoisted_82 = { class: "tree-children" };
  var _hoisted_92 = ["disabled"];
  function render3(_ctx, _cache, $props, $setup, $data, $options) {
    return openBlock2(), createElementBlock2("div", {
      class: normalizeClass2(["tree-node", { opened: $props.node.open }])
    }, [
      createBaseVNode2("span", {
        ref: "reference",
        class: normalizeClass2(["tree-link", { active: $props.node.value === $props.selected_node.value }]),
        onClick: _cache[1] || (_cache[1] = ($event) => $setup.emit("node-click", $props.node)),
        disabled: $props.node.fetching,
        onMouseover: $setup.onMouseover,
        onMouseleave: $setup.onMouseleave
      }, [
        createBaseVNode2("div", { innerHTML: $setup.icon }, null, 8, _hoisted_23),
        createBaseVNode2("a", _hoisted_33, toDisplayString2($props.node.label), 1),
        createCommentVNode2(" Icon open File record in new tab "),
        $props.node.is_leaf ? (openBlock2(), createElementBlock2("a", {
          key: 0,
          href: $setup.open_file($props.node.value),
          disabled: $props.node.fetching,
          target: "_blank",
          class: "file-doc-link ml-2",
          innerHTML: _ctx.frappe.utils.icon("external-link", "sm"),
          onClick: _cache[0] || (_cache[0] = withModifiers2(() => {
          }, ["stop"]))
        }, null, 8, _hoisted_43)) : createCommentVNode2("v-if", true)
      ], 42, _hoisted_110),
      $props.node.file_url && _ctx.frappe.utils.is_image_file($props.node.file_url) ? (openBlock2(), createElementBlock2("div", _hoisted_52, [
        withDirectives2(createBaseVNode2("div", _hoisted_62, [
          createBaseVNode2("img", {
            src: $props.node.file_url
          }, null, 8, _hoisted_72)
        ], 512), [
          [vShow2, $setup.isOpen]
        ])
      ])) : createCommentVNode2("v-if", true),
      withDirectives2(createBaseVNode2("ul", _hoisted_82, [
        (openBlock2(true), createElementBlock2(Fragment2, null, renderList2($props.node.children, (n) => {
          return openBlock2(), createBlock2($setup["TreeNode"], {
            key: n.value,
            node: n,
            selected_node: $props.selected_node,
            onNodeClick: (n2) => $setup.emit("node-click", n2),
            onLoadMore: (n2) => $setup.emit("load-more", n2)
          }, null, 8, ["node", "selected_node", "onNodeClick", "onLoadMore"]);
        }), 128)),
        $props.node.has_more_children ? (openBlock2(), createElementBlock2("button", {
          key: 0,
          class: "btn btn-xs btn-load-more",
          onClick: _cache[2] || (_cache[2] = ($event) => $setup.emit("load-more", $props.node)),
          disabled: $props.node.children_loading
        }, toDisplayString2($props.node.children_loading ? _ctx.__("Loading...") : _ctx.__("Load more")), 9, _hoisted_92)) : createCommentVNode2("v-if", true)
      ], 512), [
        [vShow2, $props.node.open]
      ])
    ], 2);
  }

  // frappe/public/js/frappe/file_uploader/TreeNode.vue
  TreeNode_default2.render = render3;
  TreeNode_default2.__file = "frappe/public/js/frappe/file_uploader/TreeNode.vue";
  TreeNode_default2.__scopeId = "data-v-877e6dee";
  var TreeNode_default = TreeNode_default2;

  // sfc-script:/home/frappe/yefri-bench/apps/frappe/frappe/public/js/frappe/file_uploader/FileBrowser.vue?type=script
  var FileBrowser_default = {
    __name: "FileBrowser",
    emits: ["hide-browser"],
    setup(__props, { expose: __expose, emit: __emit }) {
      let emit2 = __emit;
      let node = ref2({
        label: __("Home"),
        value: "Home",
        children: [],
        children_start: 0,
        children_loading: false,
        is_leaf: false,
        fetching: false,
        fetched: false,
        open: false,
        filtered: true
      });
      let selected_node = ref2({});
      let search_text = ref2("");
      let page_length = ref2(10);
      let folder_node = ref2(null);
      function toggle_node(node2) {
        if (!node2.fetched && !node2.is_leaf) {
          node2.fetching = true;
          node2.children_start = 0;
          node2.children_loading = false;
          get_files_in_folder(node2.value, 0).then(({ files, has_more }) => {
            node2.open = true;
            node2.children = files;
            node2.fetched = true;
            node2.fetching = false;
            node2.children_start += page_length.value;
            node2.has_more_children = has_more;
          });
        } else {
          node2.open = !node2.open;
          select_node(node2);
        }
      }
      function load_more(node2) {
        if (node2.has_more_children) {
          let start2 = node2.children_start;
          node2.children_loading = true;
          get_files_in_folder(node2.value, start2).then(({ files, has_more }) => {
            node2.children = node2.children.concat(files);
            node2.children_start += page_length.value;
            node2.has_more_children = has_more;
            node2.children_loading = false;
          });
        }
      }
      function select_node(node2) {
        if (node2.is_leaf) {
          selected_node.value = node2;
        }
      }
      function get_files_in_folder(folder, start2) {
        return frappe.call("frappe.core.api.file.get_files_in_folder", {
          folder,
          start: start2,
          page_length: page_length.value
        }).then((r) => {
          let { files = [], has_more = false } = r.message || {};
          files.sort((a, b) => {
            if (a.is_folder && b.is_folder) {
              return a.modified < b.modified ? -1 : 1;
            }
            if (a.is_folder) {
              return -1;
            }
            if (b.is_folder) {
              return 1;
            }
            return 0;
          });
          files = files.map((file) => make_file_node(file));
          return { files, has_more };
        });
      }
      function search_by_name() {
        if (search_text.value === "") {
          node.value = folder_node.value;
          return;
        }
        if (search_text.value.length < 3)
          return;
        frappe.call("frappe.core.api.file.get_files_by_search_text", {
          text: search_text.value
        }).then((r) => {
          let files = r.message || [];
          files = files.map((file) => make_file_node(file));
          if (!folder_node.value) {
            folder_node.value = node.value;
          }
          node.value = {
            label: __("Search Results"),
            value: "",
            children: files,
            by_search: true,
            open: true,
            filtered: true
          };
        });
      }
      function make_file_node(file) {
        let filename = file.file_name || file.name;
        let label = frappe.utils.file_name_ellipsis(filename, 40);
        return {
          label,
          filename,
          file_url: file.file_url,
          value: file.name,
          is_leaf: !file.is_folder,
          fetched: !file.is_folder,
          children: [],
          children_loading: false,
          children_start: 0,
          open: false,
          fetching: false,
          filtered: true
        };
      }
      onMounted2(() => {
        toggle_node(node.value);
      });
      __expose({ selected_node });
      const __returned__ = { get emit() {
        return emit2;
      }, set emit(v) {
        emit2 = v;
      }, get node() {
        return node;
      }, set node(v) {
        node = v;
      }, get selected_node() {
        return selected_node;
      }, set selected_node(v) {
        selected_node = v;
      }, get search_text() {
        return search_text;
      }, set search_text(v) {
        search_text = v;
      }, get page_length() {
        return page_length;
      }, set page_length(v) {
        page_length = v;
      }, get folder_node() {
        return folder_node;
      }, set folder_node(v) {
        folder_node = v;
      }, toggle_node, load_more, select_node, get_files_in_folder, search_by_name, make_file_node, onMounted: onMounted2, ref: ref2, TreeNode: TreeNode_default };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  };

  // sfc-template:/home/frappe/yefri-bench/apps/frappe/frappe/public/js/frappe/file_uploader/FileBrowser.vue?type=template
  var _hoisted_111 = { class: "file-browser" };
  var _hoisted_24 = { class: "file-browser-list" };
  var _hoisted_34 = { class: "file-filter" };
  var _hoisted_44 = ["placeholder"];
  function render4(_ctx, _cache, $props, $setup, $data, $options) {
    return openBlock2(), createElementBlock2("div", _hoisted_111, [
      createBaseVNode2("div", null, [
        createBaseVNode2("a", {
          href: "",
          class: "text-muted text-medium",
          onClick: _cache[0] || (_cache[0] = withModifiers2(($event) => $setup.emit("hide-browser"), ["prevent"]))
        }, toDisplayString2(_ctx.__("\u2190 Back to upload files")), 1)
      ]),
      createBaseVNode2("div", _hoisted_24, [
        createBaseVNode2("div", _hoisted_34, [
          withDirectives2(createBaseVNode2("input", {
            type: "search",
            class: "form-control input-xs",
            placeholder: _ctx.__("Search by filename or extension"),
            "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => $setup.search_text = $event),
            onInput: _cache[2] || (_cache[2] = ($event) => _ctx.frappe.utils.debounce($setup.search_by_name(), 300))
          }, null, 40, _hoisted_44), [
            [vModelText, $setup.search_text]
          ])
        ]),
        createVNode2($setup["TreeNode"], {
          class: "tree with-skeleton",
          node: $setup.node,
          selected_node: $setup.selected_node,
          onNodeClick: _cache[3] || (_cache[3] = (n) => $setup.toggle_node(n)),
          onLoadMore: _cache[4] || (_cache[4] = (n) => $setup.load_more(n))
        }, null, 8, ["node", "selected_node"])
      ])
    ]);
  }

  // frappe/public/js/frappe/file_uploader/FileBrowser.vue
  FileBrowser_default.render = render4;
  FileBrowser_default.__file = "frappe/public/js/frappe/file_uploader/FileBrowser.vue";
  FileBrowser_default.__scopeId = "data-v-1d966cc2";
  var FileBrowser_default2 = FileBrowser_default;

  // sfc-script:/home/frappe/yefri-bench/apps/frappe/frappe/public/js/frappe/file_uploader/WebLink.vue?type=script
  var WebLink_default = {
    __name: "WebLink",
    emits: ["hide-web-link"],
    setup(__props, { expose: __expose, emit: __emit }) {
      let emit2 = __emit;
      let url = ref2("");
      __expose({ url });
      const __returned__ = { get emit() {
        return emit2;
      }, set emit(v) {
        emit2 = v;
      }, get url() {
        return url;
      }, set url(v) {
        url = v;
      }, ref: ref2 };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  };

  // sfc-template:/home/frappe/yefri-bench/apps/frappe/frappe/public/js/frappe/file_uploader/WebLink.vue?type=template
  var _hoisted_112 = { class: "file-web-link margin-bottom" };
  var _hoisted_25 = { class: "input-group" };
  var _hoisted_35 = ["placeholder"];
  function render5(_ctx, _cache, $props, $setup, $data, $options) {
    return openBlock2(), createElementBlock2("div", _hoisted_112, [
      createBaseVNode2("a", {
        href: "",
        class: "text-muted text-medium",
        onClick: _cache[0] || (_cache[0] = withModifiers2(($event) => $setup.emit("hide-web-link"), ["prevent"]))
      }, toDisplayString2(_ctx.__("\u2190 Back to upload files")), 1),
      createBaseVNode2("div", _hoisted_25, [
        withDirectives2(createBaseVNode2("input", {
          type: "text",
          class: "form-control",
          placeholder: _ctx.__("Attach a web link"),
          "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => $setup.url = $event)
        }, null, 8, _hoisted_35), [
          [vModelText, $setup.url]
        ])
      ])
    ]);
  }

  // frappe/public/js/frappe/file_uploader/WebLink.vue
  WebLink_default.render = render5;
  WebLink_default.__file = "frappe/public/js/frappe/file_uploader/WebLink.vue";
  WebLink_default.__scopeId = "data-v-55466dd8";
  var WebLink_default2 = WebLink_default;

  // frappe/public/js/integrations/google_drive_picker.js
  var GoogleDrivePicker = class {
    constructor({ pickerCallback, enabled, appId, clientId } = {}) {
      this.scope = "https://www.googleapis.com/auth/drive.file";
      this.pickerApiLoaded = false;
      this.enabled = enabled;
      this.appId = appId;
      this.pickerCallback = pickerCallback;
      this.clientId = clientId;
    }
    async loadPicker() {
      inject_script("https://accounts.google.com/gsi/client").then(() => {
        this.authenticate();
      });
      inject_script("https://apis.google.com/js/api.js").then(() => {
        gapi.load("client:picker", {
          callback: () => {
            gapi.client.load("https://www.googleapis.com/discovery/v1/apis/drive/v3/rest");
          }
        });
      });
    }
    authenticate() {
      const tokenClient = google.accounts.oauth2.initTokenClient({
        client_id: this.clientId,
        scope: this.scope,
        callback: async (response) => {
          if (response.error !== void 0) {
            frappe.throw(response);
          }
          this.createPicker(response.access_token);
        }
      });
      tokenClient.requestAccessToken({ prompt: "" });
    }
    createPicker(access_token) {
      const docsView = new google.picker.DocsView();
      docsView.setParent("root");
      docsView.setIncludeFolders(true);
      this.picker = new google.picker.PickerBuilder().setAppId(this.appId).setOAuthToken(access_token).addView(docsView).addView(new google.picker.DocsUploadView()).setLocale(frappe.boot.lang).setCallback(this.pickerCallback).build();
      this.picker.setVisible(true);
      this.setupHide();
    }
    setupHide() {
      let bg = document.querySelectorAll(".picker-dialog-bg");
      for (const el of bg) {
        el.addEventListener("click", () => {
          this.picker.dispose();
        });
      }
    }
  };
  function inject_script(src) {
    return new Promise((resolve, reject) => {
      if (document.querySelector(`script[src="${src}"]`) !== null) {
        resolve();
        return;
      }
      let script = document.createElement("script");
      script.src = src;
      script.onload = resolve;
      script.onerror = reject;
      document.body.appendChild(script);
    });
  }

  // sfc-script:/home/frappe/yefri-bench/apps/frappe/frappe/public/js/frappe/file_uploader/ImageCropper.vue?type=script
  var import_cropperjs = __toESM(require_cropper());
  var ImageCropper_default = {
    __name: "ImageCropper",
    props: {
      file: Object,
      fixed_aspect_ratio: Number
    },
    emits: ["toggle_image_cropper"],
    setup(__props, { expose: __expose, emit: __emit }) {
      __expose();
      const props = __props;
      let emit2 = __emit;
      let aspect_ratio = ref2(props.fixed_aspect_ratio != null ? props.fixed_aspect_ratio : NaN);
      let src = ref2(null);
      let cropper = ref2(null);
      let image = ref2(null);
      let image_ref = ref2(null);
      function crop_image() {
        props.file.crop_box_data = cropper.value.getData();
        const canvas = cropper.value.getCroppedCanvas();
        const file_type = props.file.file_obj.type;
        canvas.toBlob((blob) => {
          var cropped_file_obj = new File([blob], props.file.name, {
            type: blob.type
          });
          props.file.file_obj = cropped_file_obj;
          emit2("toggle_image_cropper");
        }, file_type);
      }
      onMounted2(() => {
        if (window.FileReader) {
          let fr = new FileReader();
          fr.onload = () => src.value = fr.result;
          fr.readAsDataURL(props.file.cropper_file);
        }
        let crop_box = props.file.crop_box_data;
        image.value = image_ref.value;
        image.value.onload = () => {
          cropper.value = new import_cropperjs.default(image.value, {
            zoomable: false,
            scalable: false,
            viewMode: 1,
            data: crop_box,
            aspectRatio: aspect_ratio.value
          });
          window.cropper = cropper.value;
        };
      });
      let aspect_ratio_buttons = computed4(() => {
        return [
          {
            label: __("1:1", null, "Image Cropper"),
            value: 1
          },
          {
            label: __("4:3", null, "Image Cropper"),
            value: 4 / 3
          },
          {
            label: __("16:9", null, "Image Cropper"),
            value: 16 / 9
          },
          {
            label: __("Free", null, "Image Cropper"),
            value: NaN
          }
        ];
      });
      watch3(
        aspect_ratio,
        (value) => {
          if (cropper.value) {
            cropper.value.setAspectRatio(value);
          }
        },
        { deep: true }
      );
      const __returned__ = { props, get emit() {
        return emit2;
      }, set emit(v) {
        emit2 = v;
      }, get aspect_ratio() {
        return aspect_ratio;
      }, set aspect_ratio(v) {
        aspect_ratio = v;
      }, get src() {
        return src;
      }, set src(v) {
        src = v;
      }, get cropper() {
        return cropper;
      }, set cropper(v) {
        cropper = v;
      }, get image() {
        return image;
      }, set image(v) {
        image = v;
      }, get image_ref() {
        return image_ref;
      }, set image_ref(v) {
        image_ref = v;
      }, crop_image, get aspect_ratio_buttons() {
        return aspect_ratio_buttons;
      }, set aspect_ratio_buttons(v) {
        aspect_ratio_buttons = v;
      }, computed: computed4, onMounted: onMounted2, ref: ref2, watch: watch3, get Cropper() {
        return import_cropperjs.default;
      } };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  };

  // sfc-template:/home/frappe/yefri-bench/apps/frappe/frappe/public/js/frappe/file_uploader/ImageCropper.vue?type=template
  var _hoisted_113 = ["src", "alt"];
  var _hoisted_26 = { class: "image-cropper-actions" };
  var _hoisted_36 = {
    key: 0,
    class: "btn-group"
  };
  var _hoisted_45 = ["onClick"];
  function render6(_ctx, _cache, $props, $setup, $data, $options) {
    return openBlock2(), createElementBlock2("div", null, [
      createBaseVNode2("div", null, [
        createBaseVNode2("img", {
          ref: "image_ref",
          src: $setup.src,
          alt: $props.file.name
        }, null, 8, _hoisted_113)
      ]),
      createBaseVNode2("div", _hoisted_26, [
        createBaseVNode2("div", null, [
          $props.fixed_aspect_ratio == null ? (openBlock2(), createElementBlock2("div", _hoisted_36, [
            (openBlock2(true), createElementBlock2(Fragment2, null, renderList2($setup.aspect_ratio_buttons, (button) => {
              return openBlock2(), createElementBlock2("button", {
                type: "button",
                class: normalizeClass2(["btn btn-default btn-sm", {
                  active: isNaN($setup.aspect_ratio) ? isNaN(button.value) : button.value === $setup.aspect_ratio
                }]),
                key: button.label,
                onClick: ($event) => $setup.aspect_ratio = button.value
              }, toDisplayString2(button.label), 11, _hoisted_45);
            }), 128))
          ])) : createCommentVNode2("v-if", true)
        ]),
        createBaseVNode2("div", null, [
          $props.fixed_aspect_ratio == null ? (openBlock2(), createElementBlock2("button", {
            key: 0,
            class: "btn btn-sm margin-right",
            onClick: _cache[0] || (_cache[0] = ($event) => $setup.emit("toggle_image_cropper"))
          }, toDisplayString2(_ctx.__("Back")), 1)) : createCommentVNode2("v-if", true),
          createBaseVNode2("button", {
            class: "btn btn-primary btn-sm",
            onClick: $setup.crop_image
          }, toDisplayString2(_ctx.__("Crop")), 1)
        ])
      ])
    ]);
  }

  // frappe/public/js/frappe/file_uploader/ImageCropper.vue
  ImageCropper_default.render = render6;
  ImageCropper_default.__file = "frappe/public/js/frappe/file_uploader/ImageCropper.vue";
  ImageCropper_default.__scopeId = "data-v-21184c3b";
  var ImageCropper_default2 = ImageCropper_default;

  // sfc-script:/home/frappe/yefri-bench/apps/powerpro/powerpro/public/js/frappe/FileUploader.vue?type=script
  var FileUploader_default = {
    __name: "FileUploader",
    props: {
      show_upload_button: {
        default: true
      },
      disable_file_browser: {
        default: false
      },
      allow_multiple: {
        default: true
      },
      as_dataurl: {
        default: false
      },
      doctype: {
        default: null
      },
      docname: {
        default: null
      },
      attachment_type: {
        default: "Tipo de Adjunto no especificado"
      },
      fieldname: {
        default: null
      },
      folder: {
        default: "Home"
      },
      method: {
        default: null
      },
      on_success: {
        default: null
      },
      make_attachments_public: {
        default: null
      },
      restrictions: {
        default: () => ({
          max_file_size: null,
          max_number_of_files: null,
          allowed_file_types: [],
          crop_image_aspect_ratio: null
        })
      },
      attach_doc_image: {
        default: false
      },
      upload_notes: {
        default: null
      }
    },
    setup(__props, { expose: __expose }) {
      var _a;
      const props = __props;
      let files = ref([]);
      let file_input = ref(null);
      let file_browser = ref(null);
      let web_link = ref(null);
      let is_dragging = ref(false);
      let currently_uploading = ref(-1);
      let show_file_browser = ref(false);
      let show_web_link = ref(false);
      let show_image_cropper = ref(false);
      let crop_image_with_index = ref(-1);
      let trigger_upload = ref(false);
      let close_dialog = ref(false);
      let hide_dialog_footer = ref(false);
      let allow_take_photo = ref(false);
      let allow_web_link = ref(true);
      let google_drive_settings = ref({
        enabled: false
      });
      let wrapper_ready = ref(false);
      allow_take_photo.value = window.navigator.mediaDevices;
      if (frappe.user_id !== "Guest") {
        frappe.call({
          method: "frappe.integrations.doctype.google_settings.google_settings.get_file_picker_settings",
          callback: (resp) => {
            if (!resp.exc) {
              google_drive_settings.value = resp.message;
            }
          }
        });
      }
      if (props.restrictions.max_file_size == null) {
        frappe.call("frappe.core.api.file.get_max_file_size").then((res) => {
          props.restrictions.max_file_size = Number(res.message);
        });
      }
      if (props.restrictions.max_number_of_files == null && props.doctype) {
        props.restrictions.max_number_of_files = (_a = frappe.get_meta(props.doctype)) == null ? void 0 : _a.max_attachments;
      }
      function dragover() {
        is_dragging.value = true;
      }
      function dragleave() {
        is_dragging.value = false;
      }
      function dropfiles(e) {
        is_dragging.value = false;
        add_files(e.dataTransfer.files);
      }
      function browse_files() {
        file_input.value.click();
      }
      function on_file_input(e) {
        add_files(file_input.value.files);
      }
      function remove_file(file) {
        files.value = files.value.filter((f) => f !== file);
      }
      function toggle_image_cropper(index) {
        crop_image_with_index.value = show_image_cropper.value ? -1 : index;
        hide_dialog_footer.value = !show_image_cropper.value;
        show_image_cropper.value = !show_image_cropper.value;
      }
      function toggle_all_private() {
        let flag;
        let private_values = files.value.filter((file) => file.private);
        if (private_values.length < files.value.length) {
          flag = true;
        } else {
          flag = false;
        }
        files.value = files.value.map((file) => {
          file.private = flag;
          return file;
        });
      }
      function show_max_files_number_warning(file) {
        console.warn(
          `File skipped because it exceeds the allowed specified limit of ${max_number_of_files} uploads`,
          file
        );
        if (props.doctype) {
          MSG = __('File "{0}" was skipped because only {1} uploads are allowed for DocType "{2}"', [
            file.name,
            max_number_of_files,
            props.doctype
          ]);
        } else {
          MSG = __('File "{0}" was skipped because only {1} uploads are allowed', [
            file.name,
            max_number_of_files
          ]);
        }
        frappe.show_alert({
          message: MSG,
          indicator: "orange"
        });
      }
      function add_files(file_array) {
        let _files = Array.from(file_array).filter(check_restrictions).map((file) => {
          let is_image = file.type.startsWith("image");
          let size_kb = file.size / 1024;
          return {
            file_obj: file,
            cropper_file: file,
            crop_box_data: null,
            optimize: size_kb > 200 && is_image && !file.type.includes("svg"),
            name: file.name,
            doc: null,
            progress: 0,
            total: 0,
            failed: false,
            request_succeeded: false,
            error_message: null,
            uploading: false,
            private: !props.make_attachments_public
          };
        });
        max_number_of_files = props.restrictions.max_number_of_files;
        if (max_number_of_files && _files.length > max_number_of_files) {
          _files.slice(max_number_of_files).forEach((file) => {
            show_max_files_number_warning(file, props.doctype);
          });
          _files = _files.slice(0, max_number_of_files);
        }
        files.value = files.value.concat(_files);
        if (files.value.length === 1 && !props.allow_multiple && props.restrictions.crop_image_aspect_ratio != null) {
          if (!files.value[0].file_obj.type.includes("svg")) {
            toggle_image_cropper(0);
          }
        }
      }
      function check_restrictions(file) {
        let { max_file_size, allowed_file_types = [] } = props.restrictions;
        let is_correct_type = true;
        let valid_file_size = true;
        if (allowed_file_types && allowed_file_types.length) {
          is_correct_type = allowed_file_types.some((type) => {
            if (type.includes("/")) {
              if (!file.type)
                return false;
              return file.type.match(type);
            }
            if (type[0] === ".") {
              return file.name.toLowerCase().endsWith(type.toLowerCase());
            }
            return false;
          });
        }
        if (max_file_size && file.size != null) {
          valid_file_size = file.size < max_file_size;
        }
        if (!is_correct_type) {
          console.warn("File skipped because of invalid file type", file);
          frappe.show_alert({
            message: __('File "{0}" was skipped because of invalid file type', [file.name]),
            indicator: "orange"
          });
        }
        if (!valid_file_size) {
          console.warn("File skipped because of invalid file size", file.size, file);
          frappe.show_alert({
            message: __('File "{0}" was skipped because size exceeds {1} MB', [
              file.name,
              max_file_size / (1024 * 1024)
            ]),
            indicator: "orange"
          });
        }
        return is_correct_type && valid_file_size;
      }
      function upload_files(dialog) {
        if (show_file_browser.value) {
          return upload_via_file_browser();
        }
        if (show_web_link.value) {
          return upload_via_web_link();
        }
        if (props.as_dataurl) {
          return return_as_dataurl();
        }
        if (!files.value.length) {
          frappe.msgprint(__("Please select a file first."));
          return Promise.reject();
        }
        dialog == null ? void 0 : dialog.get_primary_btn().prop("disabled", true);
        dialog == null ? void 0 : dialog.get_secondary_btn().prop("disabled", true);
        try {
          return frappe.run_serially(files.value.map((file, i) => () => upload_file(file, i)));
        } catch (e) {
          dialog == null ? void 0 : dialog.get_primary_btn().prop("disabled", false);
          dialog == null ? void 0 : dialog.get_secondary_btn().prop("disabled", false);
          frappe.msgprint(__("Error uploading file"));
        } finally {
          dialog == null ? void 0 : dialog.get_primary_btn().prop("disabled", false);
          dialog == null ? void 0 : dialog.get_secondary_btn().prop("disabled", false);
        }
      }
      function upload_via_file_browser() {
        let selected_file = file_browser.value.selected_node;
        if (!selected_file.value) {
          frappe.msgprint(__("Click on a file to select it."));
          close_dialog.value = true;
          return Promise.reject();
        }
        close_dialog.value = true;
        return upload_file({
          library_file_name: selected_file.value
        });
      }
      function upload_via_web_link() {
        let file_url = web_link.value.url;
        if (!file_url) {
          frappe.msgprint(__("Invalid URL"));
          close_dialog.value = true;
          return Promise.reject();
        }
        file_url = decodeURI(file_url);
        close_dialog.value = true;
        return upload_file({
          file_url
        });
      }
      function return_as_dataurl() {
        let promises = files.value.map(
          (file) => frappe.dom.file_to_base64(file.file_obj).then((dataurl) => {
            file.dataurl = dataurl;
            props.on_success && props.on_success(file);
          })
        );
        close_dialog.value = true;
        return Promise.all(promises);
      }
      function upload_file(file, i) {
        currently_uploading.value = i;
        return new Promise((resolve, reject) => {
          let xhr = new XMLHttpRequest();
          xhr.upload.addEventListener("loadstart", (e) => {
            file.uploading = true;
          });
          xhr.upload.addEventListener("progress", (e) => {
            if (e.lengthComputable) {
              file.progress = e.loaded;
              file.total = e.total;
            }
          });
          xhr.upload.addEventListener("load", (e) => {
            file.uploading = false;
            resolve();
          });
          xhr.addEventListener("error", (e) => {
            file.failed = true;
            reject();
          });
          xhr.onreadystatechange = () => {
            if (xhr.readyState == XMLHttpRequest.DONE) {
              if (xhr.status === 200) {
                file.request_succeeded = true;
                let r = null;
                let file_doc = null;
                try {
                  r = JSON.parse(xhr.responseText);
                  if (r.message.doctype === "File") {
                    file_doc = r.message;
                  }
                } catch (e) {
                  r = xhr.responseText;
                }
                file.doc = file_doc;
                if (props.on_success) {
                  props.on_success(file_doc, r);
                }
                if (i == files.value.length - 1 && files.value.every((file2) => file2.request_succeeded)) {
                  close_dialog.value = true;
                }
              } else if (xhr.status === 403) {
                file.failed = true;
                let response = JSON.parse(xhr.responseText);
                file.error_message = `Not permitted. ${response._error_message || ""}.`;
                try {
                  let server_messages = JSON.parse(response._server_messages);
                  server_messages.forEach((m) => {
                    m = JSON.parse(m);
                    file.error_message += `
 ${m.message} `;
                  });
                } catch (e) {
                  console.warning("Failed to parse server message", e);
                }
              } else if (xhr.status === 413) {
                file.failed = true;
                file.error_message = "Size exceeds the maximum allowed file size.";
              } else {
                file.failed = true;
                file.error_message = xhr.status === 0 ? "XMLHttpRequest Error" : `${xhr.status} : ${xhr.statusText}`;
                let error = null;
                try {
                  error = JSON.parse(xhr.responseText);
                } catch (e) {
                }
                frappe.request.cleanup({}, error);
              }
            }
          };
          xhr.open("POST", "/api/method/upload_file", true);
          xhr.setRequestHeader("Accept", "application/json");
          xhr.setRequestHeader("X-Frappe-CSRF-Token", frappe.csrf_token);
          let form_data = new FormData();
          if (file.file_obj) {
            form_data.append("file", file.file_obj, file.name);
          }
          form_data.append("is_private", +file.private);
          form_data.append("folder", props.folder);
          if (file.file_url) {
            form_data.append("file_url", file.file_url);
          }
          if (file.file_name) {
            form_data.append("file_name", file.file_name);
          }
          if (file.library_file_name) {
            form_data.append("library_file_name", file.library_file_name);
          }
          if (props.doctype && props.docname) {
            form_data.append("doctype", props.doctype);
            form_data.append("docname", props.docname);
            form_data.append("attachment_type", props.attachment_type);
          }
          if (props.fieldname) {
            form_data.append("fieldname", props.fieldname);
          }
          if (props.method) {
            form_data.append("method", props.method);
          }
          if (file.optimize) {
            form_data.append("optimize", true);
          }
          if (props.attach_doc_image) {
            form_data.append("max_width", 200);
            form_data.append("max_height", 200);
          }
          xhr.send(form_data);
        });
      }
      function capture_image() {
        const capture = new frappe.ui.Capture({
          animate: false,
          error: true
        });
        capture.show();
        capture.submit((data_urls) => {
          data_urls.forEach((data_url) => {
            let filename = `capture_${frappe.datetime.now_datetime().replaceAll(/[: -]/g, "_")}.png`;
            url_to_file(data_url, filename, "image/png").then((file) => add_files([file]));
          });
        });
      }
      function show_google_drive_picker() {
        close_dialog.value = true;
        let google_drive = new GoogleDrivePicker(__spreadValues({
          pickerCallback: (data) => google_drive_callback(data)
        }, google_drive_settings.value));
        google_drive.loadPicker();
      }
      function google_drive_callback(data) {
        if (data.action == google.picker.Action.PICKED) {
          upload_file({
            file_url: data.docs[0].url,
            file_name: data.docs[0].name
          });
        } else if (data.action == google.picker.Action.CANCEL) {
          cur_frm.attachments.new_attachment();
        }
      }
      function url_to_file(url, filename, mime_type) {
        return fetch(url).then((res) => res.arrayBuffer()).then((buffer2) => new File([buffer2], filename, { type: mime_type }));
      }
      let upload_complete = computed2(() => {
        return files.value.length > 0 && files.value.every((file) => file.total !== 0 && file.progress === file.total);
      });
      watch2(
        files,
        (newvalue, oldvalue) => {
          if (!props.allow_multiple && newvalue.length > 1) {
            files.value = [newvalue[newvalue.length - 1]];
          }
        },
        { deep: true }
      );
      __expose({
        files,
        add_files,
        upload_files,
        toggle_all_private,
        wrapper_ready,
        close_dialog
      });
      const __returned__ = { props, get files() {
        return files;
      }, set files(v) {
        files = v;
      }, get file_input() {
        return file_input;
      }, set file_input(v) {
        file_input = v;
      }, get file_browser() {
        return file_browser;
      }, set file_browser(v) {
        file_browser = v;
      }, get web_link() {
        return web_link;
      }, set web_link(v) {
        web_link = v;
      }, get is_dragging() {
        return is_dragging;
      }, set is_dragging(v) {
        is_dragging = v;
      }, get currently_uploading() {
        return currently_uploading;
      }, set currently_uploading(v) {
        currently_uploading = v;
      }, get show_file_browser() {
        return show_file_browser;
      }, set show_file_browser(v) {
        show_file_browser = v;
      }, get show_web_link() {
        return show_web_link;
      }, set show_web_link(v) {
        show_web_link = v;
      }, get show_image_cropper() {
        return show_image_cropper;
      }, set show_image_cropper(v) {
        show_image_cropper = v;
      }, get crop_image_with_index() {
        return crop_image_with_index;
      }, set crop_image_with_index(v) {
        crop_image_with_index = v;
      }, get trigger_upload() {
        return trigger_upload;
      }, set trigger_upload(v) {
        trigger_upload = v;
      }, get close_dialog() {
        return close_dialog;
      }, set close_dialog(v) {
        close_dialog = v;
      }, get hide_dialog_footer() {
        return hide_dialog_footer;
      }, set hide_dialog_footer(v) {
        hide_dialog_footer = v;
      }, get allow_take_photo() {
        return allow_take_photo;
      }, set allow_take_photo(v) {
        allow_take_photo = v;
      }, get allow_web_link() {
        return allow_web_link;
      }, set allow_web_link(v) {
        allow_web_link = v;
      }, get google_drive_settings() {
        return google_drive_settings;
      }, set google_drive_settings(v) {
        google_drive_settings = v;
      }, get wrapper_ready() {
        return wrapper_ready;
      }, set wrapper_ready(v) {
        wrapper_ready = v;
      }, dragover, dragleave, dropfiles, browse_files, on_file_input, remove_file, toggle_image_cropper, toggle_all_private, show_max_files_number_warning, add_files, check_restrictions, upload_files, upload_via_file_browser, upload_via_web_link, return_as_dataurl, upload_file, capture_image, show_google_drive_picker, google_drive_callback, url_to_file, get upload_complete() {
        return upload_complete;
      }, set upload_complete(v) {
        upload_complete = v;
      }, computed: computed2, ref, watch: watch2, FilePreview: FilePreview_default2, FileBrowser: FileBrowser_default2, WebLink: WebLink_default2, get GoogleDrivePicker() {
        return GoogleDrivePicker;
      }, ImageCropper: ImageCropper_default2 };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  };

  // sfc-template:/home/frappe/yefri-bench/apps/powerpro/powerpro/public/js/frappe/FileUploader.vue?type=template
  var _withScopeId = (n) => (pushScopeId("data-v-b962aefe"), n = n(), popScopeId(), n);
  var _hoisted_114 = ["onDragover", "onDragleave", "onDrop"];
  var _hoisted_27 = { class: "file-upload-area" };
  var _hoisted_37 = { key: 0 };
  var _hoisted_46 = { class: "text-center" };
  var _hoisted_53 = { class: "mt-2 text-center" };
  var _hoisted_63 = /* @__PURE__ */ createStaticVNode('<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg" data-v-b962aefe><circle cx="15" cy="15" r="15" fill="var(--subtle-fg)" data-v-b962aefe></circle><path d="M13.5 22V19" stroke="var(--text-color)" stroke-linecap="round" stroke-linejoin="round" data-v-b962aefe></path><path d="M16.5 22V19" stroke="var(--text-color)" stroke-linecap="round" stroke-linejoin="round" data-v-b962aefe></path><path d="M10.5 22H19.5" stroke="var(--text-color)" stroke-linecap="round" stroke-linejoin="round" data-v-b962aefe></path><path d="M7.5 16H22.5" stroke="var(--text-color)" stroke-linecap="round" stroke-linejoin="round" data-v-b962aefe></path><path d="M21 8H9C8.17157 8 7.5 8.67157 7.5 9.5V17.5C7.5 18.3284 8.17157 19 9 19H21C21.8284 19 22.5 18.3284 22.5 17.5V9.5C22.5 8.67157 21.8284 8 21 8Z" stroke="var(--text-color)" stroke-linecap="round" stroke-linejoin="round" data-v-b962aefe></path></svg>', 1);
  var _hoisted_73 = { class: "mt-1" };
  var _hoisted_83 = ["multiple", "accept"];
  var _hoisted_93 = /* @__PURE__ */ _withScopeId(() => /* @__PURE__ */ createBaseVNode("svg", {
    width: "30",
    height: "30",
    viewBox: "0 0 30 30",
    fill: "none",
    xmlns: "http://www.w3.org/2000/svg"
  }, [
    /* @__PURE__ */ createBaseVNode("circle", {
      cx: "15",
      cy: "15",
      r: "15",
      fill: "var(--subtle-fg)"
    }),
    /* @__PURE__ */ createBaseVNode("path", {
      d: "M13.0245 11.5H8C7.72386 11.5 7.5 11.7239 7.5 12V20C7.5 21.1046 8.39543 22 9.5 22H20.5C21.6046 22 22.5 21.1046 22.5 20V14.5C22.5 14.2239 22.2761 14 22 14H15.2169C15.0492 14 14.8926 13.9159 14.8 13.776L13.4414 11.724C13.3488 11.5841 13.1922 11.5 13.0245 11.5Z",
      stroke: "var(--text-color)",
      "stroke-miterlimit": "10",
      "stroke-linecap": "square"
    }),
    /* @__PURE__ */ createBaseVNode("path", {
      d: "M8.87939 9.5V8.5C8.87939 8.22386 9.10325 8 9.37939 8H20.6208C20.8969 8 21.1208 8.22386 21.1208 8.5V12",
      stroke: "var(--text-color)",
      "stroke-miterlimit": "10",
      "stroke-linecap": "round",
      "stroke-linejoin": "round"
    })
  ], -1));
  var _hoisted_102 = { class: "mt-1" };
  var _hoisted_115 = /* @__PURE__ */ createStaticVNode('<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg" data-v-b962aefe><circle cx="15" cy="15" r="15" fill="var(--subtle-fg)" data-v-b962aefe></circle><path d="M12.0469 17.9543L17.9558 12.0454" stroke="var(--text-color)" stroke-linecap="round" stroke-linejoin="round" data-v-b962aefe></path><path d="M13.8184 11.4547L15.7943 9.47873C16.4212 8.85205 17.2714 8.5 18.1578 8.5C19.0443 8.5 19.8945 8.85205 20.5214 9.47873V9.47873C21.1481 10.1057 21.5001 10.9558 21.5001 11.8423C21.5001 12.7287 21.1481 13.5789 20.5214 14.2058L18.5455 16.1818" stroke="var(--text-color)" stroke-linecap="round" stroke-linejoin="round" data-v-b962aefe></path><path d="M11.4547 13.8184L9.47873 15.7943C8.85205 16.4212 8.5 17.2714 8.5 18.1578C8.5 19.0443 8.85205 19.8945 9.47873 20.5214V20.5214C10.1057 21.1481 10.9558 21.5001 11.8423 21.5001C12.7287 21.5001 13.5789 21.1481 14.2058 20.5214L16.1818 18.5455" stroke="var(--text-color)" stroke-linecap="round" stroke-linejoin="round" data-v-b962aefe></path></svg>', 1);
  var _hoisted_123 = { class: "mt-1" };
  var _hoisted_132 = /* @__PURE__ */ _withScopeId(() => /* @__PURE__ */ createBaseVNode("svg", {
    width: "30",
    height: "30",
    viewBox: "0 0 30 30",
    fill: "none",
    xmlns: "http://www.w3.org/2000/svg"
  }, [
    /* @__PURE__ */ createBaseVNode("circle", {
      cx: "15",
      cy: "15",
      r: "15",
      fill: "var(--subtle-fg)"
    }),
    /* @__PURE__ */ createBaseVNode("path", {
      d: "M11.5 10.5H9.5C8.67157 10.5 8 11.1716 8 12V20C8 20.8284 8.67157 21.5 9.5 21.5H20.5C21.3284 21.5 22 20.8284 22 20V12C22 11.1716 21.3284 10.5 20.5 10.5H18.5L17.3 8.9C17.1111 8.64819 16.8148 8.5 16.5 8.5H13.5C13.1852 8.5 12.8889 8.64819 12.7 8.9L11.5 10.5Z",
      stroke: "var(--text-color)",
      "stroke-linejoin": "round"
    }),
    /* @__PURE__ */ createBaseVNode("circle", {
      cx: "15",
      cy: "16",
      r: "2.5",
      stroke: "var(--text-color)"
    })
  ], -1));
  var _hoisted_142 = { class: "mt-1" };
  var _hoisted_152 = /* @__PURE__ */ _withScopeId(() => /* @__PURE__ */ createBaseVNode("svg", {
    width: "30",
    height: "30"
  }, [
    /* @__PURE__ */ createBaseVNode("image", {
      href: "/assets/frappe/icons/social/google_drive.svg",
      width: "30",
      height: "30"
    })
  ], -1));
  var _hoisted_162 = { class: "mt-1" };
  var _hoisted_172 = { class: "text-muted text-medium text-center" };
  var _hoisted_182 = { key: 1 };
  var _hoisted_192 = { class: "file-preview-area" };
  var _hoisted_202 = {
    key: 0,
    class: "file-preview-container"
  };
  var _hoisted_21 = {
    key: 1,
    class: "flex align-center"
  };
  var _hoisted_222 = { key: 0 };
  var _hoisted_232 = { key: 1 };
  var _hoisted_242 = { class: "text-muted text-medium" };
  function render7(_ctx, _cache, $props, $setup, $data, $options) {
    return openBlock(), createElementBlock("div", {
      class: "file-uploader",
      onDragover: withModifiers($setup.dragover, ["prevent"]),
      onDragleave: withModifiers($setup.dragleave, ["prevent"]),
      onDrop: withModifiers($setup.dropfiles, ["prevent"])
    }, [
      createBaseVNode("h4", null, "Tipo de Adjunto: " + toDisplayString($setup.props.attachment_type), 1),
      withDirectives(createBaseVNode("div", _hoisted_27, [
        !$setup.is_dragging ? (openBlock(), createElementBlock("div", _hoisted_37, [
          createBaseVNode("div", _hoisted_46, toDisplayString(_ctx.__("Drag and drop files here or upload from")), 1),
          createBaseVNode("div", _hoisted_53, [
            createBaseVNode("button", {
              class: "btn btn-file-upload",
              onClick: $setup.browse_files
            }, [
              _hoisted_63,
              createBaseVNode("div", _hoisted_73, toDisplayString(_ctx.__("My Device")), 1)
            ]),
            createBaseVNode("input", {
              type: "file",
              class: "hidden",
              ref: "file_input",
              onChange: $setup.on_file_input,
              multiple: $props.allow_multiple,
              accept: ($props.restrictions.allowed_file_types || []).join(", ")
            }, null, 40, _hoisted_83),
            !$props.disable_file_browser ? (openBlock(), createElementBlock("button", {
              key: 0,
              class: "btn btn-file-upload",
              onClick: _cache[0] || (_cache[0] = ($event) => $setup.show_file_browser = true)
            }, [
              _hoisted_93,
              createBaseVNode("div", _hoisted_102, toDisplayString(_ctx.__("Library")), 1)
            ])) : createCommentVNode("v-if", true),
            $setup.allow_web_link ? (openBlock(), createElementBlock("button", {
              key: 1,
              class: "btn btn-file-upload",
              onClick: _cache[1] || (_cache[1] = ($event) => $setup.show_web_link = true)
            }, [
              _hoisted_115,
              createBaseVNode("div", _hoisted_123, toDisplayString(_ctx.__("Link")), 1)
            ])) : createCommentVNode("v-if", true),
            $setup.allow_take_photo ? (openBlock(), createElementBlock("button", {
              key: 2,
              class: "btn btn-file-upload",
              onClick: $setup.capture_image
            }, [
              _hoisted_132,
              createBaseVNode("div", _hoisted_142, toDisplayString(_ctx.__("Camera")), 1)
            ])) : createCommentVNode("v-if", true),
            $setup.google_drive_settings.enabled ? (openBlock(), createElementBlock("button", {
              key: 3,
              class: "btn btn-file-upload",
              onClick: $setup.show_google_drive_picker
            }, [
              _hoisted_152,
              createBaseVNode("div", _hoisted_162, toDisplayString(_ctx.__("Google Drive")), 1)
            ])) : createCommentVNode("v-if", true)
          ]),
          createBaseVNode("div", _hoisted_172, toDisplayString($props.upload_notes), 1)
        ])) : (openBlock(), createElementBlock("div", _hoisted_182, toDisplayString(_ctx.__("Drop files here")), 1))
      ], 512), [
        [vShow, $setup.files.length === 0 && !$setup.show_file_browser && !$setup.show_web_link]
      ]),
      withDirectives(createBaseVNode("div", _hoisted_192, [
        !$setup.show_image_cropper ? (openBlock(), createElementBlock("div", _hoisted_202, [
          (openBlock(true), createElementBlock(Fragment, null, renderList($setup.files, (file, i) => {
            return openBlock(), createBlock($setup["FilePreview"], {
              key: file.name,
              file,
              onRemove: ($event) => $setup.remove_file(file),
              onToggle_private: ($event) => file.private = !file.private,
              onToggle_optimize: ($event) => file.optimize = !file.optimize,
              onToggle_image_cropper: ($event) => $setup.toggle_image_cropper(i)
            }, null, 8, ["file", "onRemove", "onToggle_private", "onToggle_optimize", "onToggle_image_cropper"]);
          }), 128))
        ])) : createCommentVNode("v-if", true),
        $props.show_upload_button && $setup.currently_uploading === -1 ? (openBlock(), createElementBlock("div", _hoisted_21, [
          createBaseVNode("button", {
            class: "btn btn-primary btn-sm margin-right",
            onClick: _cache[2] || (_cache[2] = () => $setup.upload_files())
          }, [
            $setup.files.length === 1 ? (openBlock(), createElementBlock("span", _hoisted_222, toDisplayString(_ctx.__("Upload file")), 1)) : (openBlock(), createElementBlock("span", _hoisted_232, toDisplayString(_ctx.__("Upload {0} files", [$setup.files.length])), 1))
          ]),
          createBaseVNode("div", _hoisted_242, toDisplayString(_ctx.__("Click on the lock icon to toggle public/private")), 1)
        ])) : createCommentVNode("v-if", true)
      ], 512), [
        [vShow, $setup.files.length && !$setup.show_file_browser && !$setup.show_web_link]
      ]),
      $setup.show_image_cropper && $setup.wrapper_ready ? (openBlock(), createBlock($setup["ImageCropper"], {
        key: 0,
        file: $setup.files[$setup.crop_image_with_index],
        fixed_aspect_ratio: $props.restrictions.crop_image_aspect_ratio,
        onToggle_image_cropper: _cache[3] || (_cache[3] = ($event) => $setup.toggle_image_cropper(-1)),
        onUpload_after_crop: _cache[4] || (_cache[4] = ($event) => $setup.trigger_upload = true)
      }, null, 8, ["file", "fixed_aspect_ratio"])) : createCommentVNode("v-if", true),
      $setup.show_file_browser && !$props.disable_file_browser ? (openBlock(), createBlock($setup["FileBrowser"], {
        key: 1,
        ref: "file_browser",
        onHideBrowser: _cache[5] || (_cache[5] = ($event) => $setup.show_file_browser = false)
      }, null, 512)) : createCommentVNode("v-if", true),
      $setup.show_web_link ? (openBlock(), createBlock($setup["WebLink"], {
        key: 2,
        ref: "web_link",
        onHideWebLink: _cache[6] || (_cache[6] = ($event) => $setup.show_web_link = false)
      }, null, 512)) : createCommentVNode("v-if", true)
    ], 40, _hoisted_114);
  }

  // ../powerpro/powerpro/public/js/frappe/FileUploader.vue
  FileUploader_default.render = render7;
  FileUploader_default.__file = "../powerpro/powerpro/public/js/frappe/FileUploader.vue";
  FileUploader_default.__scopeId = "data-v-b962aefe";
  var FileUploader_default2 = FileUploader_default;

  // ../powerpro/powerpro/public/js/frappe/file_uploader.js
  var powerFileUploader = class {
    constructor({
      wrapper,
      method,
      on_success,
      doctype,
      docname,
      attachment_type,
      fieldname,
      files,
      folder,
      restrictions = {},
      upload_notes,
      allow_multiple,
      as_dataurl,
      disable_file_browser,
      dialog_title,
      attach_doc_image,
      frm,
      make_attachments_public
    } = {}) {
      var _a;
      frm && frm.attachments.max_reached(true);
      if (!wrapper) {
        this.make_dialog(dialog_title);
      } else {
        this.wrapper = wrapper.get ? wrapper.get(0) : wrapper;
      }
      if (restrictions && !restrictions.allowed_file_types) {
        let allowed_extensions = (_a = frappe.sys_defaults) == null ? void 0 : _a.allowed_file_extensions;
        if (allowed_extensions) {
          restrictions.allowed_file_types = allowed_extensions.split("\n").map((ext) => `.${ext}`);
        }
      }
      let app = createApp(FileUploader_default2, {
        show_upload_button: !Boolean(this.dialog),
        doctype,
        docname,
        attachment_type,
        fieldname,
        method,
        folder,
        on_success,
        restrictions,
        upload_notes,
        allow_multiple,
        as_dataurl,
        disable_file_browser,
        attach_doc_image,
        make_attachments_public
      });
      SetVueGlobals(app);
      this.uploader = app.mount(this.wrapper);
      if (!this.dialog) {
        this.uploader.wrapper_ready = true;
      }
      watch2(
        () => this.uploader.files,
        (files2) => {
          let all_private = files2.every((file) => file.private);
          if (this.dialog) {
            this.dialog.set_secondary_action_label(
              all_private ? __("Set all public") : __("Set all private")
            );
          }
        },
        { deep: true }
      );
      watch2(
        () => this.uploader.trigger_upload,
        (trigger_upload) => {
          if (trigger_upload) {
            this.upload_files();
          }
        }
      );
      watch2(
        () => this.uploader.close_dialog,
        (close_dialog) => {
          if (close_dialog) {
            this.dialog && this.dialog.hide();
          }
        }
      );
      watch2(
        () => this.uploader.hide_dialog_footer,
        (hide_dialog_footer) => {
          if (hide_dialog_footer) {
            this.dialog && this.dialog.footer.addClass("hide");
            this.dialog.$wrapper.data("bs.modal")._config.backdrop = "static";
          } else {
            this.dialog && this.dialog.footer.removeClass("hide");
            this.dialog.$wrapper.data("bs.modal")._config.backdrop = true;
          }
        }
      );
      if (files && files.length) {
        this.uploader.add_files(files);
      }
    }
    upload_files() {
      return this.uploader.upload_files(this.dialog);
    }
    make_dialog(title) {
      this.dialog = new frappe.ui.Dialog({
        title: title || __("Upload"),
        primary_action_label: __("Upload"),
        primary_action: () => this.upload_files(),
        secondary_action_label: __("Set all private"),
        secondary_action: () => {
          this.uploader.toggle_all_private();
        },
        on_page_show: () => {
          this.uploader.wrapper_ready = true;
        }
      });
      this.wrapper = this.dialog.body;
      this.dialog.show();
      this.dialog.$wrapper.on("hidden.bs.modal", function() {
        $(this).data("bs.modal", null);
        $(this).remove();
      });
    }
  };
  frappe.provide("frappe.ui");
  frappe.ui.powerFileUploader = powerFileUploader;

  // ../powerpro/powerpro/public/js/app.bundle.js
  console.log("app.bundle.js loaded");
})();
/*!
 * Cropper.js v1.6.1
 * https://fengyuanchen.github.io/cropperjs
 *
 * Copyright 2015-present Chen Fengyuan
 * Released under the MIT license
 *
 * Date: 2023-09-17T03:44:19.860Z
 */
/*! #__NO_SIDE_EFFECTS__ */
/**
* @vue/reactivity v3.5.12
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/
/**
* @vue/runtime-core v3.5.12
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/
/**
* @vue/runtime-dom v3.5.12
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/
/**
* @vue/shared v3.5.12
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/
/**
* vue v3.5.12
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/
//# sourceMappingURL=app.bundle.TIWMEWZZ.js.map
