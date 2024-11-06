import frappe


def execute():
    create_views()


def create_views():
    frappe.db.sql("""
    CREATE OR REPLACE VIEW `viewRetention By Invoice` as
        select
            `tabPayment Entry Reference`.reference_doctype,
            `tabPayment Entry Reference`.reference_name,
            `tabPayment Entry Reference`.retention_amount,
            `tabPayment Entry`.posting_date
        from 
            `tabPayment Entry`
        join
            `tabPayment Entry Reference`
        on
            `tabPayment Entry`.name = `tabPayment Entry Reference`.parent
        and	
            `tabPayment Entry`.docstatus = 1
        and
            `tabPayment Entry Reference`.retention_amount > 0
        and
            `tabPayment Entry Reference`.reference_doctype = 'Sales Invoice'
    """)

    frappe.db.sql("""
    CREATE OR REPLACE VIEW `view607 Payments` 
    AS 
    select 
        `tabSales Invoice`.`name` AS `sinv_name`,
        sum(
            if(
                `tabSales Invoice`.`posting_date` = `tabPayment Entry`.`posting_date` and 
                `tabMode of Payment`.`type` = 'Cash' and 
                `tabSales Invoice`.`outstanding_amount` = 0,
                `tabPayment Entry Reference`.`allocated_amount`,0
            )
        ) AS `cash_payment`,
        sum(
            if(
                `tabSales Invoice`.`posting_date` = `tabPayment Entry`.`posting_date` and 
                `tabMode of Payment`.`type` = 'Bank' and 
                `tabSales Invoice`.`outstanding_amount` = 0,
                `tabPayment Entry Reference`.`allocated_amount`,0
            )
        ) AS `bank_payment`,
        sum(
            if(
                `tabSales Invoice`.`posting_date` = `tabPayment Entry`.`posting_date` and
                `tabMode of Payment`.`type` = 'Credit Card' and
                `tabSales Invoice`.`outstanding_amount` = 0,
                `tabPayment Entry Reference`.`allocated_amount`,0
            )
        ) AS `cc_payment`,
        if(
            `tabSales Invoice`.`posting_date` <> `tabPayment Entry`.`posting_date`,
            `tabSales Invoice`.`base_grand_total`,
            0
        ) AS `credit`,
        `tabPayment Entry`.`mode_of_payment` AS `mode_of_payment` 
    from    
        `tabPayment Entry` 
    join 
        `tabMode of Payment` 
    on
        `tabPayment Entry`.`mode_of_payment` = `tabMode of Payment`.`name`
    join 
        `tabPayment Entry Reference` 
    on
        `tabPayment Entry`.`name` = `tabPayment Entry Reference`.`parent`
    and 
        `tabPayment Entry`.`docstatus` = 1 
    and 
        `tabPayment Entry Reference`.`reference_doctype` = 'Sales Invoice'

    join 
        `tabSales Invoice`
    on
        `tabPayment Entry Reference`.`reference_doctype` = 'Sales Invoice'
    and 
        `tabPayment Entry Reference`.`reference_name` = `tabSales Invoice`.`name`
    and 
        `tabSales Invoice`.`docstatus` = 1
        
    group by `tabSales Invoice`.`name`

    """)