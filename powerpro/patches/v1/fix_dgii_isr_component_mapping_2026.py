# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

"""Re-run the DGII ISR synchronization for the component used by IGC.

The original patch only looked for a component named ``ISR``. IGC uses
``Impuesto Sobre la Renta Mensual``, so the original patch completed without
updating either the component or its Salary Structure rows.
"""

from powerpro.patches.v1.setup_dgii_isr_2026 import execute as sync_dgii_isr


def execute():
	sync_dgii_isr()
