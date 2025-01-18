// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.provide("power.utils");

function round_to_nearest_multiple(value, multiple) {
    return Math.ceil(value / multiple) * multiple;
}

function round_to_nearest_eighth(number) {
	return round_to_nearest_multiple(number, 1 / 8);
}

function round_to_nearest_sixteenth(number) {
	return round_to_nearest_multiple(number, 1 / 16);
}

power.utils = {
	round_to_nearest_eighth,
};
