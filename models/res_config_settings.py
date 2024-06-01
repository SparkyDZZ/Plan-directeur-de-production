from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    time_range = fields.Selection([
        ('monthly', 'Mensuel'),
        ('weekly', 'Hebdomadaire'),
        ('daily', 'Quotidien')
    ], string='Plage de temps')

    num_columns = fields.Integer(string='Nombre de colonnes')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        config_param = self.env['ir.config_parameter'].sudo()
        
        time_range = config_param.get_param('my_module.time_range', default='monthly')
        num_columns = int(config_param.get_param('my_module.num_columns', default=12))
        
        res.update(
            time_range=time_range,
            num_columns=num_columns,
        )
        return res

    @api.model
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        config_param = self.env['ir.config_parameter'].sudo()

        config_param.set_param('my_module.time_range', self.time_range)
        config_param.set_param('my_module.num_columns', self.num_columns)