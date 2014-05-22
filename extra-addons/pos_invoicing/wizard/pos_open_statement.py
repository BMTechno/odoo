# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv
from tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class pos_open_statement(osv.osv_memory):
    _inherit = 'pos.open.statement'

    def open_statement(self, cr, uid, ids, context=None):
        """
             Open the statements
             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param context: A standard dictionary
             @return : Blank Directory
        """
        data = {}
        mod_obj = self.pool.get('ir.model.data')
        statement_obj = self.pool.get('account.bank.statement')
        sequence_obj = self.pool.get('ir.sequence')
        journal_obj = self.pool.get('account.journal')
        if context is None:
            context = {}

        st_ids = []
        #YT 26/03/2012 add ('journal_users','in',(uid))
        j_ids = journal_obj.search(cr, uid, [('journal_user','=',1),('journal_users','in',(uid))], context=context)
        if not j_ids:
            raise osv.except_osv(_('No Cash Register Defined !'), _('You must define which payment method must be available through the point of sale by reusing existing bank and cash through "Accounting > Configuration > Financial Accounting > Journals". Select a journal and check the field "PoS Payment Method" from the "Point of Sale" tab. You can also create new payment methods directly from menu "PoS Backend > Configuration > Payment Methods".'))
        cr.execute("SELECT id FROM res_users WHERE shop_id = %s"% (self.pool.get('res.users').browse(cr,uid,uid,context=context).shop_id.id,))
        s_uids = map(lambda x1: x1[0], cr.fetchall())

        #_logger.info("user_id: %s - journal_id: %s"%(s_uids,j_ids))
        cr.execute("select b.name from account_bank_statement b,sale_shop s, res_users u where b.user_id = u.id and u.shop_id = s.id and b.id in %s and b.journal_id in %s and b.state='open' and s.online='False'",
                        (tuple(s_uids),tuple(j_ids)))
        stmt_names = map(lambda x1: x1[0], cr.fetchall())

        if stmt_names:
            raise osv.except_osv(_('Cash Register Open'),_('There are some old cash regiters in state open, please close the next cash register: %s'%stmt_names))

        for journal in journal_obj.browse(cr, uid, j_ids, context=context):

            if journal.sequence_id:
                number = sequence_obj.next_by_id(cr, uid, journal.sequence_id.id)
            else:
                number = sequence_obj.next_by_code(cr, uid, 'account.cash.statement')

            data.update({
                'journal_id': journal.id,
                'user_id': uid,
                'state': 'draft',
                'name': number 
            })
            statement_id = statement_obj.create(cr, uid, data, context=context)
            st_ids.append(int(statement_id))
            
            if journal.auto_cash:
                statement_obj.button_open(cr, uid, [statement_id], context)

        tree_res = mod_obj.get_object_reference(cr, uid, 'point_of_sale', 'view_cash_statement_pos_tree')
        tree_id = tree_res and tree_res[1] or False
        form_res = mod_obj.get_object_reference(cr, uid, 'account', 'view_bank_statement_form2')
        form_id = form_res and form_res[1] or False
        search_res = mod_obj.get_object_reference(cr, uid, 'account', 'view_account_bank_statement_filter')
        search_id = search_res and search_res[1] or False
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('List of Cash Registers'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.bank.statement',
            'domain': str([('id', 'in', st_ids)]),
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'search_view_id': search_id,
        }
    
pos_open_statement()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
