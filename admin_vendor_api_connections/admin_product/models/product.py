# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

def RemoveLeadingZero(s):
    try:
        int(s)
        return str(int(s))
    except ValueError:
        return s

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    default_code = fields.Char(string='Material Code / SKU')
    categ_id = fields.Many2one('product.category', string='Material Group')
    categ_id_code = fields.Char(string="Material Group Code")
    company_code = fields.Char(string="Company Code")
    product_uom_code = fields.Char(string="UoM Code")
    po_uom_code = fields.Char(string="PO UoM Code")

    def name_get(self):
        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        self.browse(self.ids).read(['name', 'default_code'])
        return [(template.id, '%s%s' % (template.default_code and '[%s] ' % RemoveLeadingZero(template.default_code) or '', template.name))
                for template in self]

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            self.company_code = self.company_id.code

    @api.onchange('company_code')
    def onchange_company_code(self):
        if self.company_code:
            company = self.env['res.company'].sudo().search([('code', '=', self.company_code)], limit=1)
            if company[:1]:
                self.company_id = company.id

    @api.onchange('categ_id')
    def onchange_categ_id(self):
        if self.categ_id:
            self.categ_id_code = self.categ_id.code

    @api.onchange('categ_id_code')
    def onchange_categ_id_code(self):
        if self.categ_id_code:
            category_id = self.env['product.category'].sudo().search([('code', '=', self.categ_id_code)], limit=1)
            if category_id:
                self.categ_id = category_id.id

    @api.onchange('uom_id')
    def onchange_uom_id(self):
        if self.uom_id:
            self.product_uom_code = self.uom_id.code

    @api.onchange('product_uom_code')
    def onchange_product_uom_code(self):
        if self.product_uom_code:
            uom_id = self.env['uom.uom'].sudo().search([('code', '=', self.product_uom_code)], limit=1)
            if uom_id:
                self.uom_id = uom_id.id

    @api.onchange('uom_po_id')
    def onchange_uom_po_id(self):
        if self.uom_po_id:
            self.po_uom_code = self.uom_po_id.code

    @api.onchange('po_uom_code')
    def onchange_po_uom_code(self):
        if self.po_uom_code:
            uom_po_id = self.env['uom.uom'].sudo().search([('code', '=', self.po_uom_code)], limit=1)
            if uom_po_id:
                self.uom_po_id = uom_po_id.id

    @api.model
    def create(self, values):
        res = super(ProductTemplate, self).create(values)
        if res:
            res.onchange_company_code()
            res.onchange_categ_id_code()
            res.onchange_product_uom_code()
            res.onchange_po_uom_code()
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    default_code = fields.Char('Material Code / SKU')

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            self.company_code = self.company_id.code

    @api.onchange('company_code')
    def onchange_company_code(self):
        if self.company_code:
            company = self.env['res.company'].sudo().search([('code', '=', self.company_code)], limit=1)
            if company[:1]:
                self.company_id = company.id

    @api.onchange('categ_id')
    def onchange_categ_id(self):
        if self.categ_id:
            self.categ_id_code = self.categ_id.code

    @api.onchange('categ_id_code')
    def onchange_categ_id_code(self):
        if self.categ_id_code:
            category_id = self.env['product.category'].sudo().search([('code', '=', self.categ_id_code)], limit=1)
            if category_id:
                self.categ_id = category_id.id

    @api.onchange('uom_id')
    def onchange_uom_id(self):
        if self.uom_id:
            self.product_uom_code = self.uom_id.code

    @api.onchange('product_uom_code')
    def onchange_product_uom_code(self):
        if self.product_uom_code:
            uom_id = self.env['uom.uom'].sudo().search([('code', '=', self.product_uom_code)], limit=1)
            if uom_id:
                self.uom_id = uom_id.id

    @api.onchange('uom_po_id')
    def onchange_uom_po_id(self):
        if self.uom_po_id:
            self.po_uom_code = self.uom_po_id.code

    @api.onchange('po_uom_code')
    def onchange_po_uom_code(self):
        if self.po_uom_code:
            uom_po_id = self.env['uom.uom'].sudo().search([('code', '=', self.po_uom_code)], limit=1)
            if uom_po_id:
                self.uom_po_id = uom_po_id.id

    @api.model
    def create(self, values):
        res = super(ProductProduct, self).create(values)
        if res:
            res.onchange_company_code()
            res.onchange_categ_id_code()
            res.onchange_product_uom_code()
            res.onchange_po_uom_code()
        return res

    def name_get(self):
        # TDE: this could be cleaned a bit I think

        def _name_get(d):
            name = d.get('name', '')
            code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
            if code:
                name = '[%s] %s' % (RemoveLeadingZero(code),name)
            return (d['id'], name)

        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        else:
            partner_ids = []
        company_id = self.env.context.get('company_id')

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights("read")
        self.check_access_rule("read")

        result = []

        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        # Use `load=False` to not call `name_get` for the `product_tmpl_id`
        self.sudo().read(['name', 'default_code', 'product_tmpl_id'], load=False)

        product_template_ids = self.sudo().mapped('product_tmpl_id').ids

        if partner_ids:
            supplier_info = self.env['product.supplierinfo'].sudo().search([
                ('product_tmpl_id', 'in', product_template_ids),
                ('name', 'in', partner_ids),
            ])
            # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
            # Use `load=False` to not call `name_get` for the `product_tmpl_id` and `product_id`
            supplier_info.sudo().read(['product_tmpl_id', 'product_id', 'product_name', 'product_code'], load=False)
            supplier_info_by_template = {}
            for r in supplier_info:
                supplier_info_by_template.setdefault(r.product_tmpl_id, []).append(r)
        for product in self.sudo():
            variant = product.product_template_attribute_value_ids._get_combination_name()

            name = variant and "%s (%s)" % (product.name, variant) or product.name
            sellers = []
            if partner_ids:
                product_supplier_info = supplier_info_by_template.get(product.product_tmpl_id, [])
                sellers = [x for x in product_supplier_info if x.product_id and x.product_id == product]
                if not sellers:
                    sellers = [x for x in product_supplier_info if not x.product_id]
                # Filter out sellers based on the company. This is done afterwards for a better
                # code readability. At this point, only a few sellers should remain, so it should
                # not be a performance issue.
                if company_id:
                    sellers = [x for x in sellers if x.company_id.id in [company_id, False]]
            if sellers:
                for s in sellers:
                    seller_variant = s.product_name and (
                        variant and "%s (%s)" % (s.product_name, variant) or s.product_name
                        ) or False
                    mydict = {
                              'id': product.id,
                              'name': seller_variant or name,
                              'default_code': RemoveLeadingZero(s.product_code) or RemoveLeadingZero(product.default_code),
                              }
                    temp = _name_get(mydict)
                    if temp not in result:
                        result.append(temp)
            else:
                mydict = {
                          'id': product.id,
                          'name': name,
                          'default_code': RemoveLeadingZero(product.default_code),
                          }
                result.append(_name_get(mydict))
        return result


class ProductCategory(models.Model):
    _inherit = "product.category"
    _description = "Material Group"

    code = fields.Char(string="Code")
    parent_id = fields.Many2one('product.category', 'Parent Group', index=True, ondelete='cascade')
    parent_code = fields.Char(string='Parent Group Code')
    child_id = fields.One2many('product.category', 'parent_id', 'Child Group')

    @api.onchange('parent_id')
    def onchange_parent_id(self):
        if self.parent_id:
            self.parent_code = self.parent_id.code

    @api.onchange('parent_code')
    def onchange_parent_code(self):
        if self.parent_code:
            parent_id = self.env['product.category'].sudo().search([('code', '=', self.parent_code)], limit=1)
            if parent_id[:1]:
                self.parent_id = parent_id.id

    @api.model
    def create(self, vals):
        res = super(ProductCategory,self).create(vals)
        res.onchange_parent_code()
        return res


class UomUom(models.Model):
    _inherit = 'uom.uom'

    code = fields.Char(string='Code')
    category_code = fields.Char(string='Category Code')
    category_id = fields.Many2one('uom.category', 'Category', required=False, ondelete='cascade',
        help="Conversion between Units of Measure can only occur if they belong to \
        the same category. The conversion will be made based on the ratios.")

    @api.onchange('category_id')
    def onchange_category_id(self):
        if self.category_id:
            self.category_code = self.category_id.code

    @api.onchange('category_code')
    def onchange_category_code(self):
        if self.category_code:
            category_id = self.env['uom.category'].sudo().search([('code', '=', self.category_code)], limit=1)
            if category_id[:1]:
                self.category_id = category_id.id

    @api.model
    def create(self, vals):
        res = super(UomUom,self).create(vals)
        res.onchange_category_code()
        return res


class UomCategory(models.Model):
    _inherit = 'uom.category'

    code = fields.Char(string='UOM Code')


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    company_code = fields.Char(string="Company Code")

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            self.company_code = self.company_id.code

    @api.onchange('company_code')
    def onchange_company_code(self):
        if self.company_code:
            company = self.env['res.company'].sudo().search([('code', '=', self.company_code)], limit=1)
            if company[:1]:
                self.company_id = company.id

    @api.model
    def create(self, vals):
        res = super(ProductSupplierinfo,self).create(vals)
        res.onchange_company_code()
        return res


class ProductClassification(models.Model):
    _name = 'product.classification'
    _description = 'Product Classification'

    name = fields.Char(string='Name', required=True)
