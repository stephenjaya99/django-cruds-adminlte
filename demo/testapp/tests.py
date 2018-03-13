# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.urls import reverse
from django.contrib.auth.models import User, Permission, Group
from django.test.client import RequestFactory
from django.utils import timezone
from django.template import Template, Context
from django.db.models.query_utils import Q
from django.urls.exceptions import NoReverseMatch
from django.conf import settings
# TEST
from django.test import ( TestCase,
                            Client )

# CRUD
from cruds_adminlte.utils import get_fields
from cruds_adminlte import utils
from cruds_adminlte import crud as crud_views
from cruds_adminlte.filter import ( FormFilter, 
                                    get_filters )


DELETE='delete'
UPDATE='update'
LIST='list'
CREATE='create'
DETAIL='detail'
# APPs
from testapp.views import (AutorCRUD, 
                           InvoiceCRUD, 
                           IndexView, 
                           CustomerCRUD, 
                           LineCRUD, 
                           AddressCRUD,
                           filterAddress,
                           LineForm,
                           Lines_AjaxCRUD,
                           Address_AjaxCRUD,
                           )

from testapp.forms import (CustomerForm,
                           InvoiceForm,
                           LineForm,
                           AddressesForm) 
from testapp.models import ( Autor, 
                             Addresses, 
                             Customer, 
                             Invoice, 
                             Line )


# others
import math
from datetime import datetime, timedelta, tzinfo
import urllib 


""" function to return the url """
def get_action_url(test,action,pk=None):
            if ( action in [UPDATE,DELETE,DETAIL] ) :
                    url= reverse(test.app_testing+'_'+test.model+'_'+action, kwargs={'pk': pk})    # testapp/invoice/1/update
            else:
                    url= reverse(test.app_testing+'_'+test.model+'_'+action)    # testapp/invoice/create   -   testapp/invoice/list
                    
            if (test.view.namespace and test.type==LIST): # if have namespace, find URL action on /namespace/
                if (test.view.cruds_url) and ( action in [CREATE,UPDATE,DELETE,DETAIL] ): # cruds_url is in url actions and that changes the url 
                        url=url.replace(test.view.cruds_url, 'namespace')  
            return url

    
def get_build_params(test,params=[],strseparator="&",str_boolean=False):
    query='?'
    separator=False
    for index in params :
         value=index[1]  
         if value!='' :  
             if separator :
                query+=strseparator
                separator=False;    
             if str_boolean:
                value= value if value!= 'on'  else True
                
             if  isinstance(value, (str, int) ):    
                query+="%s=%s"%(index[0], value)
             else:
                for i in value:
                    if separator :
                        query+=strseparator
                        separator=False;    
                    query+="%s=%s"%(index[0], i)
                    separator=True
                    
             separator=True
    return query    
    
        
""" Fathers class  """   
class TreeData(TestCase):
    def setUp(self):
        self.app_testing='testapp'
        #self.model='invoice'
        nobjects=4 # number of objects to insert           
        self.actions=[CREATE, LIST, DELETE, UPDATE, DETAIL]  
        
        self.factory = RequestFactory()
        #user to test
        self.user = User( username='test', email='test@example.com', is_active=True,
              is_staff=True, is_superuser=True,
        )
        self.user.set_password('test')
        self.user.save()
        
        
        # add objects Autor/Addressses
        for i in range(nobjects):  # add Autor-Address 
             # autor 0   | autor 1   | autor 2   | autor 3
             # address 0 | address 1 | address 2 | address 3
            
             ao = Autor.objects.create(name="author_name_%i"%i)
             ado = Addresses(autor=ao)
             ado.name="addresses_address_%s_%i"%(ao.pk,i)
             ado.city="addresses_city_%s_%i"%(ao.pk,i)
             ado.save()
              
          
          
        # add object Customer/Invoices
        for i in range(nobjects):  # add Customer (Invoices < Lines)
            co = Customer.objects.create(name="customer_%i"%i,
                                          information="information_customer_%i"%i,
                                          email="customer_%i@examples.dj"%i,
                                         date = datetime.now(),
                                         time=datetime.now(),
                                         datetime=timezone.now()
                                         )
            # customer 0 | customer 1 | customer 2 | customer 3
            # -----------| ---------- | ---------- | ----------
            # invoice 0  | invoice 4  | invoice 8  | invoice 12
            # invoice 1  | invoice 5  | invoice 9  | invoice 13
            # invoice 2  | invoice 6  | invoice 10 | invoice 14
            # invoice 3  | invoice 7  | invoice 11 | invoice 15
                                                   
            Invoice.objects.create(customer=co,registered=True,sent=False,paid=False,date=timezone.now())  # only registered   
            Invoice.objects.create(customer=co,registered=True,sent=True,paid=False,date=timezone.now()) # registered and sent
            Invoice.objects.create(customer=co,registered=False,sent=False,paid=False,date=timezone.now()) # nothing did!
            Invoice.objects.create(customer=co,registered=True,sent=True,paid=True,date=timezone.now())  # completed

                      
        # add object Invoices / Lines
        for io in Invoice.objects.all():
             for i in range(nobjects):  
                 lo=Line(invoice=io)
                 lo.reference=io.customer.name+"_"+str(io.pk)+"_reference_"+str(i)  #  customer_0 + 0 + _reference + 0
                 lo.concept=io.customer.name+"_"+str(io.pk)+"_concept_"+str(i)   #  customer_0 + 0 + _concept + 0
                 lo.quantity="quantity_"+str(i)      #  quantity_0
                 lo.unit=i
                 lo.unit_price=i
                 lo.amount=i
                 lo.save()
                 # ( customer 0) -------------------------------------------------------------------------------------------
                 # invoice 0                                           | invoice 1
                 #   * Line 0 i=0                                      |  *   Line 4    i=0
                 #Line.reference=customer_0_0_reference_0              | Line.reference=customer_0_1_reference_0 
                 #Line.concept=customer_0_0_concept_0                  | Line.concept=customer_0_1_concept_0
                 #Line.concept=quantity_0                              | Line.concept=quantity_0           
                 #   * Line 1 i=1                                      |   *  Line 5    i=1
                 #Line.reference=customer_0_0_reference_1              | Line.reference=customer_0_5_reference_1           
                 #Line.concept=customer_0_0_concept_1                  | Line.reference=customer_0_5_concept_1                   
                 #Line.concept=quantity_1                              | Line.concept=quantity_1  
                 #   * Line 2 i=2  ...                                 |   *  Line 6   i=2   ...
                 #   * Line 3 i=3  ...                                 |   *  Line 7   i=3   ...              
                 #----------                      ----------------------------------                      -----------------   
                 # invoice 2                                           | invoice 3
                 #   * Line 8   i=0                                    |  *   Line 12   i=0
                 #Line.reference=customer_0_0_reference_0              | Line.reference=customer_0_1_reference_0 
                 #Line.concept=customer_0_0_concept_0                  | Line.concept=customer_0_1_concept_0
                 #Line.concept=quantity_0                              | Line.concept=quantity_0              
                 #   *  Line 9  i=1                                    |   *  Line 13   i=1
                 #Line.reference=customer_0_0_reference_1              | Line.reference=customer_0_1_reference_1           
                 #Line.concept=customer_0_0_concept_1                  | Line.reference=customer_0_1_concept_1                   
                 #Line.concept=quantity_1                              | Line.concept=quantity_1  
                 #   * Line 10 i=2  ...                                |   *  Line 14  i=2   ...
                 #   * Line 11 i=3  ...                                |   *  Line 15  i=3   ...                 
                 # ( customer 1) -------------------------------------------------------------------------------------------                
class SimpleOListViewTest:
   

        """ Test definition of number objects inserted """
        def test_count_objects(self):
               count=self.view.model.objects.count()
               self.assertEqual(count, self.model_inserting)
                  
        """ Test show list of 'object_list' """
        def test_get_listView_content(self):
            self.client.login(username='test', password='test')
            self.type=LIST
            url= get_action_url(self,self.type)         

            response = self.client.get(url)
            if ( self.type in self.view.views_available):
                self.assertEqual(response.status_code, 200 )
            else:
                 self.assertEqual(response.status_code, 404 )
            
            if self.view.paginate_by :
                object_list=response.context['object_list']
                if (( len(object_list) == self.model_inserting) and (self.model_inserting < self.view.paginate_by)):
                    self.assertEqual(len(object_list), self.model_inserting)  # Number of objects
                else:
                   self.assertEqual(len(object_list), self.view.paginate_by)  # Number of object by pages
                   
            self.assertEqual(self.view.views_available, response.context['views_available'])
            
              
                                        
            self.client.logout()   
        
        """ Test show only button of valid actions """         
        def test_get_listView_actions(self):
            self.client.login(username='test', password='test')
            self.type=LIST
            url= get_action_url(self,self.type)        
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200 )
            for action in self.actions:  # django actions [CREATE, LIST, DELETE, UPDATE, DETAIL]
                 if action in self.view.views_available:  # crudview set actions [CREATE, LIST]
                     if action not in self.ignore_action : 
                         firstobject= self.view.model.objects.first()
                         self.assertTrue(isinstance(firstobject, self.view.model)) # check if return something
                         url=get_action_url(self,action,firstobject.pk)
                         self.assertContains( response, '<a href="'+url )  # check if exist hyperlink to actions
                         
              
            self.client.logout()   
            
            
        """ Test show object by pagination 1  and url pages buttons """         
        def test_get_listView_pagination(self):
            
            
            self.client.login(username='test', password='test')
            self.type=LIST
            url= get_action_url(self,self.type)        
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200 )
            if self.view.paginate_by :
                paginations=response.context['page_obj']
                
                if (self.model_inserting<=self.view.paginate_by): # only one page
                    self.assertTrue( ("<Page 1 of 1>") in ("%s"%paginations) ) # check page 1
                else: # more of one page
                    pages=int(math.ceil((self.model_inserting/self.view.paginate_by))) # number of pages to show all objects    
                    strcheck= ("<Page 1 of %i>"%pages)             
                    self.assertTrue( strcheck in ("%s"%paginations),"Could %s don't have %i pages"%(strcheck,pages)) # check page 1
                    
                    
                    # exist all buttons of paginations
                    if('enumeration.html' in self.view.paginate_template ):  # Numeric pagination template: cruds/pagination/enumeration.html
                        for i in range(1, pages):  # 16 = (4 custormers x 4 invoices)
                            html='page=%i"> %i </a>'%(i,i)
                            self.assertContains( response, "%s"%html)  
                            self.assertTemplateUsed(response,  self.view.paginate_template)# loaded the correct template 
                                
                    if('prev_next.html' in self.view.paginate_template ):  # default pagination template: cruds/pagination/prev_next.html
                            html='<a href="?page=2"' 
                            self.assertContains( response, "%s"%html)   
                            self.assertTemplateUsed(response, self.view.paginate_template) # loaded the correct template 
                            
            self.client.logout()    
            
            
        """ Test show only the list of fields settings   """
        def test_get_listview_fields(self):
            self.client.login(username='test', password='test')
            self.type=LIST
            url= get_action_url(self,self.type)      
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200 )
            
            fields=response.context['fields']  # columns fields to build table html
            
            if self.view.template_name_base != crud_views.CRUDView.template_name_base : # test if used custom template
                    tmp=self.app_testing +'/'+ self.model+'/'+self.view.template_name_base+'/list.html'
                    self.assertTemplateUsed(response,tmp )       # loaded the correct template 
                
             
            model_fields= utils.get_fields(self.view.model)   
            if self.view.list_fields and self.view.fields!='__all__':   # test if fields exist on response
                for field in self.view.list_fields :
                     self.assertIn(field,model_fields)   # fields exist on model
                     self.assertIn(field,fields)         # fields exist on listview setting list_fields
                     html='<th class="th-field-%s th-fieldtype-'%(field) 
                     self.assertContains( response, "%s"%html)            # column field exist on table html
            else: # '__all__'
                for field in model_fields:
                    if not field == 'id':
                        self.assertIn(field,fields)         # field exist on listview setting list_fields
                        html='<th class="th-field-%s th-fieldtype-'%(field) 
                        self.assertContains( response, "%s"%html) # column field exist on table html
            
            self.client.logout()    
             
class FilterOListViewTest:
    """ Test show only the list of list_filter settings   """
    def test_get_listview_fields_filters(self):
            self.client.login(username='test', password='test')
            self.type=LIST
            url= get_action_url(self,self.type)         
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200 )
            
            view_filter= self.view.list_filter          
            if view_filter :                  
                 for filter in view_filter:
                     if (isinstance(filter, str)):
                         filter_html='<label for="id_%s">'%filter
                         self.assertContains(response,filter_html)   # label filters exist
                     elif hasattr(filter,'form'):
                            if hasattr(filter.form,'base_fields'):
                                for bf in filter.form.base_fields:
                                     filter_html='<label for="id_%s">'%bf
                                     self.assertContains(response,filter_html)   # label filters exist
                     
                                        
                 self.assertContains(response,'<input type="text" name="q" value="" class="form-control"')   # input search exist                     
            self.client.logout()  
            
            
            
    """ Test action url with filters params invalid, checking to add one by one """
    def test_get_listView_pagination_and_filters_invalid(self):
            params=[]
            self.client.login(username='test', password='test')
            self.type=LIST
            url= get_action_url(self,self.type) 
                       
            view_filter= self.view.list_filter    
             
          
             
            if view_filter:         # check filters params
                sfilter=None
                response = self.client.get(url)
                object_list=self.view.model.objects.all()
                self.assertEqual(response.status_code, 200 )
                for filter in view_filter :
                        
                         if (isinstance(filter, str)):
                             if filter in self.filter_params_false:
                                     value= self.filter_params_false[filter] 
                                     params.append([filter,value])
                                     
                                     if value !='' :  
                                        value= value if value!= 'on' else 1  # 1 == True
                                        value= value if value!= 'off' else 0  #  0 == False   
                                        sfilter = Q(**{filter: value})
                                        object_list = object_list.filter(sfilter) 
                                        
                             else:
                                    params.append([filter,''])       
                         elif hasattr(filter,'form'):
                                if hasattr(filter.form,'base_fields'):
                                    for bf in filter.form.base_fields:
                                         filter=bf
                                         value= self.filter_params_false[filter] 
                                         params.append([filter,value])                                         
                                         sfilter = {"%s__in"%filter: self.filter_params_false[filter]}
                                         object_list = object_list.filter(**sfilter)   
               

                         objects=object_list.count()                             
                         pm=get_build_params(self,params) # params  ?customer&....
                         urlparams=url+pm

                         response = self.client.get(urlparams)
                         self.assertEqual(response.status_code, 200, urlparams )
                         

                         if(objects==0): # result no items
                                self.assertContains( response, '<td>No items yet.</td>')
                                
                         else:       
                             if self.view.paginate_by :  # check paginations
                                paginations=response.context['page_obj']                            
                                if (objects<= self.view.paginate_by): # only one page)
                                    self.assertTrue( ("<Page 1 of 1>") in ("%s"%paginations), urlparams) # check page 1
                                else: # more of one page                               
                                    # exist all buttons of paginations
                                    if('enumeration.html' in self.view.paginate_template ):  # Numeric pagination template: cruds/pagination/enumeration.html
                                        pages=int(math.ceil((self.filter_nresults/self.view.paginate_by))) # number of pages to show all objects  
                                        for i in range(1, pages):                                              
                                            pm=get_build_params(self,params,'&amp;',True)
                                            pageurl=pm+'&amp;page=%i'%i
                                            html='<a href="%s"'%pageurl 
                                            self.assertContains( response, '%s'%html )  
                                            self.assertTemplateUsed(response,  self.view.paginate_template)# loaded the correct template 
                                                
                                    if('prev_next.html' in self.view.paginate_template ):  # default pagination template: cruds/pagination/prev_next.html
                                            html='<a href="?page=2"' 
                                            self.assertContains( response, "%s"%html)   
                                            self.assertTemplateUsed(response, self.view.paginate_template) # loaded the correct template 
                                            

                                          
            self.client.logout()   
            
    """ Test action url with filters params valid, checking to add one by one """
    def test_get_listView_pagination_and_filters_valid(self):
            params=[]
            self.client.login(username='test', password='test')
            self.type=LIST
            url= get_action_url(self,self.type) 
                       
            view_filter= self.view.list_filter    
             
          
             
            if view_filter:         # check filters params
                sfilter=None
                response = self.client.get(url)
                object_list=self.view.model.objects.all()
                self.assertEqual(response.status_code, 200 )
                for filter in view_filter :
                        
                         if (isinstance(filter, str)):
                             if filter in self.filter_params_true:
                                     value= self.filter_params_true[filter] 
                                     params.append([filter,value])
                                     
                                     if value !='' :  
                                        value= value if value!= 'on' else 1  # 1 == True 
                                        sfilter = Q(**{filter: value})
                                        object_list = object_list.filter(sfilter) 
                                        
                             else:
                                    params.append([filter,''])       
                         elif hasattr(filter,'form'):
                                if hasattr(filter.form,'base_fields'):
                                    for bf in filter.form.base_fields:
                                         filter=bf
                                         value= self.filter_params_true[filter] 
                                         params.append([filter,value])                                         
                                         sfilter = {"%s__in"%filter: self.filter_params_true[filter]}
                                         object_list = object_list.filter(**sfilter)   
               

                         objects=object_list.count()                             
                         pm=get_build_params(self,params) # params  ?customer&....
                         urlparams=url+pm

                         response = self.client.get(urlparams)
                         self.assertEqual(response.status_code, 200, urlparams )
                         

                         if(objects==0): # result no items
                                self.assertContains( response, '<td>No items yet.</td>')
                                
                         else:       
                             if self.view.paginate_by :  # check paginations
                                paginations=response.context['page_obj']                            
                                if (objects<= self.view.paginate_by): # only one page)
                                    self.assertTrue( ("<Page 1 of 1>") in ("%s"%paginations), urlparams) # check page 1
                                else: # more of one page                               
                                    # exist all buttons of paginations
                                    if('enumeration.html' in self.view.paginate_template ):  # Numeric pagination template: cruds/pagination/enumeration.html
                                        pages=int(math.ceil((self.filter_nresults/self.view.paginate_by))) # number of pages to show all objects  
                                        for i in range(1, pages):                                              
                                            pm=get_build_params(self,params,'&amp;',True)
                                            pageurl=pm+'&amp;page=%i'%i
                                            html='<a href="%s"'%pageurl 
                                            self.assertContains( response, '%s'%html )  
                                            self.assertTemplateUsed(response,  self.view.paginate_template)# loaded the correct template 
                                                
                                    if('prev_next.html' in self.view.paginate_template ):  # default pagination template: cruds/pagination/prev_next.html
                                            html='<a href="?page=2"' 
                                            self.assertContains( response, "%s"%html)   
                                            self.assertTemplateUsed(response, self.view.paginate_template) # loaded the correct template 
                                            

                                          
            self.client.logout()  

class SimpleOEditViewTest:
    update_set=None
    
    """ Test show list of 'object_list' """
    def test_get_editView_content(self):
            self.client.login(username='test', password='test')
            firstobject= self.view.model.objects.first()
            self.assertTrue(isinstance(firstobject, self.view.model)) # check if return something
            self.type=UPDATE
            if (self.type in self.view.views_available):
                url= get_action_url(self,self.type,firstobject.pk)    
                response = self.client.get(url)  
                self.assertEqual(response.status_code, 200 )
            
                if self.view.template_name_base != crud_views.CRUDView.template_name_base : # test if used custom template
                        tmp=self.app_testing +'/'+ self.model+'/'+self.view.template_name_base+'/update.html'
                        self.assertTemplateUsed(response,tmp )       # loaded the correct template 
                        
                        
                if ( DELETE in self.view.views_available ):                       
                        url_delete= get_action_url(self,DELETE,firstobject.pk)
                        
                        # when cruds_url exist in view, that check the url with namespace
                        if  hasattr(self.view, 'cruds_url') : # cruds_url is in url actions and that changes the url 
                            # If cruds_url exist on view, the DELETE action should have 'namespace'
                            url_delete=url_delete.replace(self.view.cruds_url, 'namespace')  
                            
                        html= '%s'%( url_delete ) # When it have a A.href or Form.action
                        self.assertContains(response,html)      
                        
     
                    
                fields=response.context['fields']  # columns fields to build table html 
                model_fields= utils.get_fields(self.view.model)   
                if self.view.fields and not self.view.fields=='__all__':   # test if fields exist on response
                    for field in self.view.fields :
                         self.assertIn(field,model_fields)   # fields exist on model
                         self.assertIn(field,fields)         # fields exist on update view setting fields
                         html='<div id="div_id_%s" '%(field) 
                         self.assertContains( response, "%s"%html)            # column field exist on table html
                else: # '__all__'
                    for field in model_fields:
                        if not field == 'id':
                            self.assertIn(field,fields)         # field exist on update view setting fields
                            html='<div id="div_id_%s" '%(field) 
                            self.assertContains( response, "%s"%html) # column field exist on table html
                
                
                if self.view.inlines:
                    for inline in self.view.inlines :         
                        inline_model_fields= utils.get_fields(inline.model)   
                        html= '<div data-refresh-url="/inline/testapp/%s/%i/list" id="%s'%(inline.name,firstobject.pk,inline.name)
                        self.assertContains(response,html)     



                self.assertEqual(self.view.views_available, response.context['views_available'])  
                  
                        
            else:
                try:
                     url= get_action_url(self,self.type,firstobject.pk)
                     response = self.client.get(url)
                     self.assertEqual(response.status_code, 404 ) 
                except NoReverseMatch :
                    pass
                           
 
            self.client.logout() 
                  
    
    """ Test save changes on method post"""
    def  test_post_editview_valid(self):
            self.type=UPDATE
            self.client.login(username='test', password='test')
            
            firstobject= self.view.model.objects.first()
            self.assertTrue(isinstance(firstobject, self.view.model)) 

            if (self.type in self.view.views_available):
                url= get_action_url(self,self.type,firstobject.pk)
                url_list=get_action_url(self,LIST,firstobject.pk)
                                    
                response = self.client.get(url)  
                self.assertEqual(response.status_code, 200 )
                form=response.context['form']

    
                if self.update_set:
                    data = form.initial 
                  
                    # set new value to fields 
                    for attr in self.update_set:
                        data[attr]= self.update_set[attr]

                    response=self.client.post(url, data)  # sending changes
                    # checked if save and after show listview
                    self.assertRedirects(response, 
                                         url_list, status_code=302, 
                                         target_status_code=200, 
                                         fetch_redirect_response=True) 
                    # Re-get view whith news inputs values
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200 )  
                    # check values changed of DB
                    for attr in self.update_set:
                        newvalue=str(self.update_set[attr])  
                        formvalue=response.context['form'][attr].value()
                        # format of insert values
                        if( isinstance(formvalue, datetime) ): 
                            newvalue=str(datetime.strptime(newvalue, "%m/%d/%Y").date())
                        # format of DB values
                        if not ( isinstance(formvalue, str) ):
                           formvalue=str(formvalue)       
                        self.assertTrue((newvalue  in formvalue) ,"Value  %s not in %s, it did not have been changed to DB"%(newvalue,formvalue) )
            self.client.logout() 
            
    """ Check display error to requerid fields """
    def  test_post_editview_invalid(self):
            self.type = UPDATE
            self.client.login(username='test', password='test')
            
            firstobject = self.view.model.objects.first()
            self.assertTrue(isinstance(firstobject, self.view.model)) 

            if (self.type in self.view.views_available):
                url = get_action_url(self, self.type, firstobject.pk)
                url_list = get_action_url(self, LIST, firstobject.pk)
                                    
                response = self.client.get(url)  
                self.assertEqual(response.status_code, 200)
                form = response.context['form']
    
                if self.update_set:
                    data = form.initial 
                    response = self.client.post(url, data)  # sending changes
                    # checked if save doesn't completed by requered field error
                    self.assertEqual(response.status_code, 200)
                    
                    # only return code 200 when form have been need a field valid
                    if (response.status_code == 200):
                        form = response.context['form']                    
                        html = '<ul class="errorlist">'
                        self.assertTrue((html in str(form)), "Error with value field  (%s) doesn't showed" % html)
    
                        # set new value to fields 
                        for attr in self.update_set:
                            data[attr] = self.update_set[attr]
    
                        response = self.client.post(url, data)  # sending changes
                        # checked if save and after show listview
                        self.assertRedirects(response,
                                             url_list, status_code=302,
                                             target_status_code=200,
                                             fetch_redirect_response=True) 

            self.client.logout() 
     
class FilterOEditViewTest:
    
       
    """ Test if editview use filters params"""
    def  test_editview_filters(self): 
            self.type=UPDATE
            params=[]
            view_filter= self.view.list_filter   
            self.client.login(username='test', password='test')
            firstobject= self.view.model.objects.first()
            self.assertTrue(isinstance(firstobject, self.view.model)) 
            url=get_action_url(self,self.type,firstobject.pk) 
            if view_filter:         # check filters params
                for filter in view_filter :
                         if (isinstance(filter, str)):
                             if filter in self.filter_params_true:
                                    value= self.filter_params_true[filter]                                     
                                    value= value if value!= 'on' else True  # 1 == True

                                    params.append([filter,value])                                            
                         elif hasattr(filter,'form'):
                                if hasattr(filter.form,'base_fields'):
                                    for bf in filter.form.base_fields:
                                         filter=bf
                                         value= self.filter_params_true[filter] 
                                         params.append([filter,value])
                         pm=get_build_params(self,params) # params  ?customer&....            
                         urlparams=url+pm  # add params to url base

                         # Get view with params of filters
                         response = self.client.get(urlparams)
                         self.assertEqual(response.status_code, 200, "Response doesn't completed with current data" )
                         
                         
                         filter_html='<form action="%s'%(urlparams)
                         self.assertContains(response,filter_html,1,200,"The form actions doesn't have been completed whith the filters url")   # label filters exist

class SimpleODeleteViewTest:
    
    """ check if comands post do the deleting  """
    def  test_deleteview_post_delete(self): 
        self.type=DELETE # delete form update/edit view
        self.client.login(username='test', password='test')
            
        lastobject = self.view.model.objects.last()
         
        if (self.type in self.view.views_available):
            url = get_action_url(self, self.type, lastobject.pk)
            
            response = self.client.post(url)  # sending delete
            # check if delete request is completed
            self.assertEqual(response.status_code, 302) # then code do not confirm delete
            
            
            response = self.client.post(url)  # sending delete
            # check if have been deleted and show error 404
            self.assertEqual(response.status_code, 404) # the response do not sent to error of pk valid                
        self.client.logout()    
        

    def  test_deleteview_get_delete(self): 
        self.type=DELETE # delete form update/edit view
        self.client.login(username='test', password='test')
            
        lastobject = self.view.model.objects.last()
         
        if (self.type in self.view.views_available):
            url = get_action_url(self, self.type, lastobject.pk)
            
            response = self.client.get(url)  # sending delete
            # check if delete request send to confirmation delete view
            self.assertEqual(response.status_code, 200)
            
            if (response.status_code == 200):
                #form = response.context['form']                    
                html = '<button type="submit" class="btn btn-danger">'
                self.assertContains( response, "%s"%html) # delete view have confirmation question?
         
            
        self.client.logout()         

""" Auth user access """
class AuthUserViewTest:
         
    def test_user_noLogin(self):
        """ The User don't have been login """
        response = self.client.get(reverse('auth_user_list'))
        self.assertEqual(response.status_code, 302 )
        self.assertEqual(response.url,"/accounts/login/?next=/lte/auth/user/list")
         
         
    """ user  out log on list """          
    def  test_user_list_noLogin(self):
        self.type=LIST
        if (self.type in self.view.views_available):        
            url= get_action_url(self,self.type)         
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302 )        
            self.assertEqual(response.url,"/accounts/login/?next=%s"%url);
        
    """ user  out log on edit """     
    def test_user_edit_noLogin(self):
        self.type=UPDATE
        if (self.type in self.view.views_available):
            
            firstobject= self.view.model.objects.first()
            self.assertTrue(isinstance(firstobject, self.view.model)) # check if return something
            url= get_action_url(self,self.type,firstobject.pk)         
            response = self.client.get(url)            
            
            self.assertEqual(response.status_code, 302 ) 
            self.assertEqual(response.url,"/accounts/login/?next=%s"%url);        
        
    """ user  out log on create """    
    def test_user_create_noLogin(self):
        self.type=CREATE
        if (self.type in self.view.views_available):
            url= get_action_url(self,self.type)         
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 302 ) 
            self.assertEqual(response.url,"/accounts/login/?next=%s"%url);       
        
    """ user  out log on delete """           
    def test_user_delete_noLogin(self):
        self.type=DELETE
        if (self.type in self.view.views_available):
            
            firstobject= self.view.model.objects.first()
            self.assertTrue(isinstance(firstobject, self.view.model)) # check if return something
            url= get_action_url(self,self.type,firstobject.pk)         
            response = self.client.get(url)           
        
            self.assertEqual(response.status_code, 302 )      
            self.assertEqual(response.url,"/accounts/login/?next=%s"%url);   
         
    """ user  logging on list """                    
    def  test_user_listview_Login(self):
        self.type=LIST
        if (self.type in self.view.views_available):
            self.client.login(username='test', password='test')        
            url= get_action_url(self,self.type)         
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 200 )        
        
    """ user  logging on edit """
    def test_user_editview_Login(self):
        self.type=UPDATE
        if (self.type in self.view.views_available):
            self.client.login(username='test', password='test') 
            
            firstobject= self.view.model.objects.first()
            self.assertTrue(isinstance(firstobject, self.view.model)) # check if return something
            url= get_action_url(self,self.type,firstobject.pk)         
            response = self.client.get(url)     

            self.assertEqual(response.status_code, 200 )   
        
    """ user  logging on create """    
    def test_user_createview_Login(self):
        self.type=CREATE
        if (self.type in self.view.views_available):
            self.client.login(username='test', password='test')
            url= get_action_url(self,self.type)         
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 200 ) 
        
    """ user  logging on delete """        
    def test_user_deleteview_Login(self):
        self.type=DELETE
        if (self.type in self.view.views_available):
            self.client.login(username='test', password='test') 
            
            firstobject= self.view.model.objects.first()
            self.assertTrue(isinstance(firstobject, self.view.model)) # check if return something
            url= get_action_url(self,self.type,firstobject.pk)         
            response = self.client.get(url)     
    
            self.assertEqual(response.status_code, 200 )      
        
                 
#     def test_user_list(self):
#         """ The user can load the users list,  when it's login """
#         self.client.login(username='test', password='test')
#         response = self.client.get(reverse('auth_user_list'))
#         #print (response)
#         self.assertEqual(response.status_code, 200 )
#         self.assertQuerysetEqual(response.context['object_list'],['<User: test>'])
         
         
#     def test_user_group_list(self): 
#         """ The user can lad group, when it's login """
#         self.client.login(username='test', password='test')
#         response = self.client.get(reverse('auth_user_groups_list'))
#         #print (response)
#         self.assertQuerysetEqual(response.context['object_list'], [])
#                 

""" Children class   """    
class AutorTest(TreeData,SimpleOListViewTest,FilterOListViewTest,SimpleOEditViewTest,SimpleODeleteViewTest,AuthUserViewTest):   
         def __init__(self, *args, **kwargs):
                 self.model='autor'        
                 self.model_inserting=4
                 self.ignore_action = []   
                 self.view = AutorCRUD()   # defined view 
                 super(AutorTest, self).__init__(*args, **kwargs)                        
  
class AddressTest(TreeData,SimpleOListViewTest,FilterOListViewTest,SimpleOEditViewTest,SimpleODeleteViewTest,AuthUserViewTest):   
         def __init__(self, *args, **kwargs):
                 self.model='addresses'        
                 self.model_inserting=4      # 4 = (4 addresses)
                 self.ignore_action = []   
                 self.view = AddressCRUD()   # defined view 
                 super(AddressTest, self).__init__(*args, **kwargs)
  
class LineTest(TreeData,SimpleOListViewTest,FilterOListViewTest,SimpleOEditViewTest,SimpleODeleteViewTest,AuthUserViewTest):   
         def __init__(self, *args, **kwargs):
                 self.model='line' 
                 self.model_inserting=(4*4*4)  # 64 = (4 custormers x 4 invoices x 4 line)
                 self.ignore_action=[LIST]   # Used when action doesn't is shows. Example:: list action on sidebar
                 self.view = LineCRUD()   # defined view
                 super(LineTest, self).__init__(*args, **kwargs)
                                                                  
class InvoiceTest(TreeData,SimpleOListViewTest,FilterOListViewTest,SimpleOEditViewTest,SimpleODeleteViewTest,FilterOEditViewTest,AuthUserViewTest):   
        def __init__(self, *args, **kwargs):
                self.model='invoice' 
                self.model_inserting=(4*4)   #  16 = (4 custormers x 4 invoices)
                self.ignore_action = []
                self.filter_params_false={'customer': '1','sent':'on',  'line':[1,2,3,4]} # Invalid values | use the list_filter order 
                self.filter_params_true={'customer': '1','sent':'on','paid':'on', 'line':[5,6,7,8]} # Valid values  | use the list_filter order 
                self.filter_nresults=2   # check only show two row or pages result
                self.update_set = { 'registered' : True, 'sent': True, 'date':'12/01/2011','total': '1000' }
                self.view = InvoiceCRUD()   # defined view 
                super(InvoiceTest, self).__init__(*args, **kwargs)

class CustomerTest(TreeData,SimpleOListViewTest,FilterOListViewTest,SimpleOEditViewTest,SimpleODeleteViewTest,FilterOEditViewTest,AuthUserViewTest):   
        def __init__(self, *args, **kwargs):
                self.model='customer'        
                self.model_inserting=4
                self.ignore_action = []   
                self.view = CustomerCRUD()   # defined view
                super(CustomerTest, self).__init__(*args, **kwargs)  
                 
       


                

#    
# """ Admin user views test"""
# class AdminViewTestCase(TestCase):
#     def setUp(self):
#         group_name = "My Test Group"
#         self.group = Group(name=group_name)
#         self.group.save()
#         
#         self.user = User(
#             username='test', email='test@example.com', is_active=True,
#             is_staff=True, is_superuser=True,
#         )
#         self.user.set_password('test')
#         self.user.save()
#         self.client.login(username='test', password='test')
#         
#         
#     def tearDown(self):
#         self.client.logout()
#                     
#     def test_user_can_access(self):
#         """user in group should have access
#         """
#         self.user.groups.add(self.group)
#         self.user.save()
#         self.client.login(username='test', password='test')
#         response = self.client.get(reverse('auth_user_list'))
#         self.assertEqual(response.status_code, 200)      
#         
#             
#     def test_admin_not_broken(self):
#         """ user can use django admin """
#         response = self.client.get('/admin/')
#         self.assertContains(response, '/admin/password_change/')
#         self.assertNotContains(response, "You don't have permission to edit anything")
# 
#     def test_admin_auth_not_broken(self):
#         """ user can init auth """
#         response = self.client.get('/admin/auth/')
#         self.assertEqual(response.status_code, 200, response)
