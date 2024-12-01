# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ItemGenerator(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		autonomy: DF.Int
		autonomy_uom: DF.Link | None
		brand: DF.Link | None
		capacity: DF.Float
		capacity_uom: DF.Link | None
		capcidad_udm: DF.Link | None
		color: DF.Link | None
		conectividad: DF.Link | None
		current: DF.Link | None
		custom: DF.Literal["", "Bordado", "Grabado", "Impreso"]
		depth: DF.Float
		depth_uom: DF.Link | None
		description: DF.LongText | None
		diameter: DF.Float
		diameter_uom: DF.Link | None
		finish: DF.Link | None
		flavour: DF.Link | None
		frequency: DF.Literal["", "50Hz", "60Hz"]
		garantía: DF.Int
		garantía_udm: DF.Link | None
		gauge: DF.Float
		gauge_uom: DF.Link | None
		height: DF.Float
		height_uom: DF.Link | None
		item: DF.Link | None
		material: DF.Link | None
		model: DF.Data | None
		packaging: DF.Link | None
		pcs: DF.Int
		phase: DF.Link | None
		presentation: DF.Float
		presentation_uom: DF.Link | None
		production_capacity: DF.Int
		shape: DF.Literal["", "Circular", "Cuadrado(a)", "Curvo", "Ovalado(a)", "Rectangular", "Triangular"]
		size: DF.Data | None
		spec1: DF.Link | None
		spec2: DF.Link | None
		use: DF.Link | None
		voltage: DF.Link | None
		weight: DF.Float
		weight_uom: DF.Link | None
		width: DF.Float
		width_uom: DF.Link | None
		year: DF.Literal["", "1970", "1971", "1972", "1973", "1974", "1975", "1976", "1977", "1978", "1979", "1980", "1981", "1982", "1983", "1984", "1985", "1986", "1987", "1988", "1989", "1990", "1991", "1992", "1993", "1994", "1995", "1996", "1997", "1998", "1999", "2000", "2001", "2002", "2003", "2004", "2005", "2006", "2007", "2008", "2009", "2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"]
	# end: auto-generated types
	pass
