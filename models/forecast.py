from odoo import models, fields, api

class ForecastedQty(models.Model):
    _name = 'mps.forecasted.qty'
    _description = 'Forecasted Quantity'

    name = fields.Char(string="Nom", readonly=True)
    quantity = fields.Float(string='Quantity')
    date_start = fields.Date(string='Date debut')
    date_end = fields.Date(string='Date de fin')
    starting_inventory_qty = fields.Float(string="Starting Inventory Quantity", compute='_compute_starting_inventory_qty')

    mps_id = fields.Many2one('mps', string="Master Production Schedule", ondelete='cascade')

    @api.depends('mps_id', 'date_start', 'date_end')
    def _compute_starting_inventory_qty(self):
        for record in self:
            previous_inventory = self.search([
                ('mps_id', '=', record.mps_id.id),
                ('date_start', '<', record.date_start),
                ('date_end', '>', record.date_start)
            ], order='date_start desc', limit=1)
            record.starting_inventory_qty = previous_inventory.quantity if previous_inventory else 0.0

    def _get_sales_orders(self, date_start, date_end):
        return self.env['sale.order.line'].search([
            ('product_id', '=', self.mps_id.product_id.id),
            ('order_id.state', 'in', ['sale', 'done']),
            ('order_id.date_order', '>=', f'{date_start}'),
            ('order_id.date_order', '<=', f'{date_end}')
        ])

    def get_actual_demand_y2(self):
        sales_orders = self._get_sales_orders(self.date_start, self.date_end)
        return sum(sales_orders.mapped('product_uom_qty'))

    def get_actual_demand_y1(self):
        sales_orders = self._get_sales_orders(self.date_start, self.date_end)
        return sum(sales_orders.mapped('product_uom_qty'))      

    def get_actual_demand(self, start_date, end_date):
        sales_orders = self._get_sales_orders(start_date, end_date)
        return sum(sales_orders.mapped('product_uom_qty'))