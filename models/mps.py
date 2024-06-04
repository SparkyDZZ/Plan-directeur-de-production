from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class MPS(models.Model):
    _name = 'mps'
    _description = 'Master Production Schedule'

    display_name = fields.Char(string="Nom d'affichage", compute='_compute_display_name', store=True)
    bom_id = fields.Many2one('mrp.bom', string="Nomenclature")
    forecast_ids = fields.One2many('mps.forecasted.qty', 'mps_id', string="Quantité prévue à la date")
    forecast_target_qty = fields.Float(string="Stock de sécurité", default="0")
    max_to_replenish_qty = fields.Float(string="Maximum à réapprovisionner", default=1000)
    min_to_replenish_qty = fields.Float(string="Minimum à réapprovisionner")
    product_id = fields.Many2one('product.product', string="Produit")
    product_tmpl_id = fields.Many2one('product.template', string="Modèle de produit", required=True)
    product_uom_id = fields.Many2one('uom.uom', string="Unité de mesure du produit")
    warehouse_id = fields.Many2one('stock.warehouse', string="Entrepôt")
    has_indirect_demand = fields.Boolean(string="Has indirect demand", default=0)

    @api.constrains('product_tmpl_id')
    def _check_unique_product_tmpl_id(self):
        for record in self:
            if record.product_tmpl_id:
                existing_record = self.search([
                    ('id', '!=', record.id),
                    ('product_tmpl_id', '=', record.product_tmpl_id.id),
                ])
                if existing_record:
                    raise ValidationError("Ce produit existe déja!")

    @api.depends('product_id')
    def _compute_display_name(self):
        for record in self:
            if record.product_id:
                record.display_name = f"{record.product_id.display_name}"


    def create_forecasted_qty(self):
        for mps_record in self:
            periods = mps_record.generate_periods()
            for period in periods:
                vals = {
                    'mps_id': mps_record.id,
                    'date_start': period['period_start'],
                    'date_end': period['period_end'],
                }
                t=self.env['mps.forecasted.qty'].create(vals)
                print(f"HELOOOOOOO {t.actual_demand_qty}")

    @api.model
    def create(self, vals):
        bom_id = vals.get('bom_id')
        product_tmpl_id = vals.get('product_tmpl_id')
        product_id = vals.get('product_id')
        product_uom_id = vals.get('product_uom_id')

        if product_tmpl_id and (not product_id) :
            product_tmpl = self.env['product.template'].browse(product_tmpl_id)
            product_id = product_tmpl.product_variant_id.id
            product_uom_id = product_tmpl.uom_id.id

        mps_record = super(MPS, self).create({
            **vals,
            'product_id': product_id,
            'product_uom_id': product_uom_id,
        })

        if bom_id:
            bom = self.env['mrp.bom'].browse(bom_id)
            for line in bom.bom_line_ids:
                mps_line_vals = {
                    'product_id': line.product_id.id,
                    'product_tmpl_id' : line.product_id.product_tmpl_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'warehouse_id' : vals.get('warehouse_id'),
                    'max_to_replenish_qty' : 1000,
                    'min_to_replenish_qty' : 0,
                    'has_indirect_demand' : 1,
                }
                self.env['mps'].create(mps_line_vals)
        mps_record.create_forecasted_qty()

        return mps_record

    @api.model
    def save(self, vals):
        return {'type': 'ir.actions.act_window_close'}

    def action_delete(self):
        for rec in self:
            rec.unlink()

    def generate_periods(self):
        config_param = self.env['ir.config_parameter'].sudo()
        time_range = config_param.get_param('my_module.time_range', default='monthly')
        num_columns = int(config_param.get_param('my_module.num_columns', default=2))
        
        start_date = datetime.now()
        periods = []

        for i in range(num_columns):
            if time_range == 'daily':
                period_start = start_date + timedelta(days=i)
                period_end = period_start + timedelta(days=1) - timedelta(seconds=1)
                period_str = period_start.strftime("%B %d").capitalize()
            elif time_range == 'weekly':
                week_start = start_date + timedelta(weeks=i)
                week_end = week_start + timedelta(days=6)
                period_str = f"Week {week_start.isocalendar()[1]} ({week_start.day}-{week_end.day}/{week_start.strftime('%b')})"
                period_start = week_start
                period_end = week_end
            elif time_range == 'monthly':
                period_start = start_date + timedelta(days=30*i)
                period_end = period_start + timedelta(days=29)
                period_str = period_start.strftime("%b. %Y").capitalize()
            else:
                raise ValidationError("Invalid time range configuration!")

            periods.append({
                'period_str': period_str,
                'period_start': period_start,
                'period_end': period_end,
            })
        
        return periods