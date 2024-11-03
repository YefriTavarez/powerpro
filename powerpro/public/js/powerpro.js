jQuery(frappe.router).ready(async function () {
	await frappe.timeout(.300);

	const reroute_if_accounts_receivable = function (route_options) {
		const route = frappe.get_route();

		if (route.length === 2) {
			if (route[0] === "query-report" && route[1] === "Accounts Receivable") {
				frappe.set_re_route("query-report", "Accounts Receivable Reloaded", route_options);
			}
		}
	};

	const reroute_if_accounts_receivable_summary = function (route_options) {
		const route = frappe.get_route();

		// looking for route ['query-report', 'Stock Balance']
		if (route.length === 2) {
			if (route[0] === "query-report" && route[1] === "Accounts Receivable Summary") {
				frappe.set_re_route("query-report", "Accounts Receivable Summary Reloaded", route_options);
			}
		}
	};

	// other reroutes go here and added to the runner below

	const do_reroutes = function (route_options) {
		frappe.run_serially([
			() => reroute_if_accounts_receivable(route_options),
			() => reroute_if_accounts_receivable_summary(route_options),
		]);
	};

	// jQuery(window).on("hashchange", function (event) {
	// 	do_reroutes(frappe.route_options);
	// });

	frappe.router.on("change", function(event) {
		do_reroutes({ ...frappe.route_options });
	});
	
	(function () {
		do_reroutes({ ...frappe.route_options });
	})();
});
