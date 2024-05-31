from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MPS(models.Model):
    _name = 'mps'
    _description = 'Master Production Schedule'

    bom_id = fields.Many2one('mrp.bom', string="Nomenclature")
    display_name = fields.Char(string="Nom d'affichage", readonly=True)
    forecast_ids = fields.One2many('mps.forecasted.qty', 'mps_id', string="Quantité prévue à la date")
    forecast_target_qty = fields.Float(string="Stock de sécurité")
    max_to_replenish_qty = fields.Float(string="Maximum à réapprovisionner", default=1000)
    min_to_replenish_qty = fields.Float(string="Minimum à réapprovisionner")
    product_id = fields.Many2one('product.product', string="Produit")
    product_tmpl_id = fields.Many2one('product.template', string="Modèle de produit")
    product_uom_id = fields.Many2one('uom.uom', string="Unité de mesure du produit")
    warehouse_id = fields.Many2one('stock.warehouse', string="Entrepôt")
    period_id = fields.Many2one('mps.period', string="Période")


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

    @api.model
    def save(self, vals):
        return {'type': 'ir.actions.act_window_close'}

    def action_delete(self):
        for rec in self:
            rec.unlink()