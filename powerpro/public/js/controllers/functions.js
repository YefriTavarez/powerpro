// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

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

function round_to_nearest_sixteenth(number) {
	return round_to_nearest_multiple(number, 1 / 16);
}

power.utils = {
	round_to_nearest_eighth,
};
