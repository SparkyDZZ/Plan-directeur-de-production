from odoo import http
import xmlrpc.client

class ProductController(http.Controller):

    @http.route('/get_products', type='json', auth='public')
    def get_products(self):
        # Connect to the Odoo XML-RPC server
        url = 'http://localhost:8069'
        db = 'PFE'
        username = 'odoo15'
        password = 'P@ssw0rd'
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        uid = common.authenticate(db, username, password, {})
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

        # Fetch products using the XML-RPC call
        products = models.execute_kw(db, uid, password, 'product.product', 'search_read', [[]], {'fields': ['id', 'name']})
        
        # Return the products as JSON response
        return 'hello'
