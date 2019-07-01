''' Lib for Plugin
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '0.9.01 2019-03-28'
Content
    See github.com/kvichans/cuda_kv_dlg/wiki
ToDo: (see end of file)
'''

import  sys, os, tempfile, json, re
from    time        import perf_counter

import          cudatext        as app
from            cudatext    import ed
import          cudax_lib       as apx
try:    from    cuda_kv_base    import *    # as separated plugin
except: from     .cd_kv_base    import *    # as part of this plugin

VERSION     = re.split('Version:', __doc__)[1].split("'")[1]
VERSION_V,  \
VERSION_D   = VERSION.split(' ')

def version():  return VERSION_V

_       = None
try:
    _   = get_translation(__file__) # I18N
except:pass

pass;                           _log4mod = LOG_FREE             # Order log in the module
    
_TYPE_ABBRS  = {
     'labl': 'label'
    ,'lilb': 'linklabel'
    ,'edit': 'edit'
    ,'edtp': 'edit_pwd'
    ,'sped': 'spinedit'
    ,'memo': 'memo'
    ,'bttn': 'button'
    ,'rdio': 'radio'
    ,'chck': 'check'
    ,'chbt': 'checkbutton'
    ,'chgp': 'checkgroup'
    ,'rdgp': 'radiogroup'
    ,'cmbx': 'combo'
    ,'cmbr': 'combo_ro'
    ,'libx': 'listbox'
    ,'clbx': 'checklistbox'
    ,'livw': 'listview'
    ,'clvw': 'checklistview'
    ,'tabs': 'tabs'
    ,'clpn': 'colorpanel'
    ,'imag': 'image'
    ,'flbx': 'filter_listbox'
    ,'flvw': 'filter_listview'
    ,'bvel': 'bevel'
    ,'panl': 'panel'
    ,'grop': 'group'
    ,'splt': 'splitter'
    ,'pags': 'pages'
    ,'trvw': 'treeview'
    ,'edtr': 'editor'
    ,'stbr': 'statusbar'
    ,'btex': 'button_ex'
    }
_TYPE_WITH_VALUE  = {
     'edit'
    ,'edit_pwd'
    ,'spinedit'
    ,'memo'
    ,'radio'
    ,'check'
    ,'checkbutton'
    ,'checkgroup'
    ,'radiogroup'
    ,'combo'
    ,'combo_ro'
    ,'listbox'
    ,'checklistbox'
    ,'listview'
    ,'checklistview'
    ,'tabs'
    ,'filter_listbox'
    ,'filter_listview'
#   ,'grop'
#   ,'splt'
#   ,'pags'
#   ,'trvw'
#   ,'edtr'
#   ,'stbr'
#   ,'btex'
    }
_ATTR_ABBRS  = {
     'cols': 'columns'
    ,'au'  : 'autosize'
    ,'ali' : 'align'
    ,'sto' : 'tab_stop'
    ,'tor' : 'tab_order'
    }
_ATTR_TP_ABBRS  = {**_ATTR_ABBRS, 'tp':'type'}
#_ATTR_TP_ABBRS  = upd_dict(_ATTR_ABBRS, {'tp':'type'})
_LIVE_ATTRS     = {'r', 'b', 'x', 'y', 'w', 'h', 'val', 'columns', 'cols', 'cols_ws', 'items'}
_LIVE_CALC_ATTRS= {'r', 'b'}

CB_HIDE = lambda ag,name,d='':None                              # Control callback to hide dlg
def CBP_WODATA(cb_user):                                        # Callback-proxy to skip data
    return lambda ag,name,d='':cb_user(ag,name)

ALI_CL  = app.ALIGN_CLIENT
ALI_LF  = app.ALIGN_LEFT
ALI_RT  = app.ALIGN_RIGHT
ALI_TP  = app.ALIGN_TOP
ALI_BT  = app.ALIGN_BOTTOM

SCROLL_W= app.app_proc(app.PROC_GET_GUI_HEIGHT, 'scrollbar')

class DlgAg:
    # See github.com/kvichans/cuda_kv_dlg/wiki

    @staticmethod
    def version():  return VERSION_V
    
    ###############
    ## Creators
    ###############
    
    
    def __del__(self):
        _dlg_proc(self.did, app.DLG_FREE)       if self.did else 0
    def __init__(self, ctrls, form, vals=None, fid=None, opts=None):
        """ Create dialog """
        pass;                   log4fun=0                       # Order log in the function
        # Fields
        self._retval= None                                      # Last event src-cid or user pointed val to return from show()
        self._hidden= True                                      # State of form
        self._dockto= ''                                        # State of form
        self._modal = None                                      # State of form
        self._onetime   = False                                 # Free form data on hide
        self._skip_free = False                                 # To ban to free form data

        self.opts   = opts.copy() if opts else {}
        ctrl_to_meta= self.opts.get('ctrl_to_meta', 'by_os')
        self._c2m   = ctrl_to_meta=='need'  or \
                      ctrl_to_meta=='by_os' and \
                        'mac'==get_desktop_environment()        # Need to translate 'Ctrl+' to 'Meta+' in hint,...
        
        self.did    = app.dlg_proc(0, app.DLG_CREATE)
        self.ctrls  = None                                      # Mem-attrs of all controls {cid:{k:v}}
        self.form   = None                                      # Mem-attrs of form         {k:v}
        
        self._setup(ctrls, form, vals, fid)

        self.gen_repro_code()
       #def __init__
    
    
    def show(self, on_exit=None, modal=True, onetime=True):
        """ Show the dialog 
                on_exit     Call the function after dlg was hidden
                modal       Show as modal or nonmodal
                onetime     Free resources (if True) after or wait next show() (if False)
            Return (if modal):  (retval, vals) 
                retval      Value of param ag.hide(retval) or None
                vals        Last live val properties of all controls
        """
        pass;                   log4fun=0                       # Order log in the function
        pass;                   log__('modal, self._dockto, onetime, ed={}', (modal, self._dockto, onetime, ed)      ,__=(log4fun,_log4mod))
        if not self.did:
            raise ValueError('Dialog data is already destroyed (see "onetime" parameter)')
        
        self._modal     = modal if not self._dockto else False
        self._retval    = None
        self._hidden    = False
        self._onetime   = onetime

        ed_caller   = ed    if self._modal else None

        def when_close():
            pass;               log__("self.fattr('p')={}",self.fattr('p')      ,__=(log4fun,_log4mod))
            if not self.fattr('p'):         # Not docked
                _form_acts('save', did=self.did
                          ,key4store=self.opts.get('form data key'))
            for cid in self.opts.get('store_col_widths', []):
                self._cols_serv('save-ws', cid=cid)
            if callable(on_exit):
                on_exit(self)
            vals    = self.vals(live=True)  if self._modal else None
            if onetime:
                if self._modal:
                    _dlg_proc(self.did, app.DLG_FREE)
                else:
                    app.timer_proc(app.TIMER_START_ONE, lambda tag:app.dlg_proc(int(tag)
                                      , app.DLG_FREE)
                                  ,200                        ,tag=             str(self.did)
                                  )
                self.did    = 0
        
            ed_to_focus = self.opts.get('on_exit_focus_to_ed', ed_caller)
            pass;               log__('ed_to_focus={}',ed_to_focus      ,__=(log4fun,_log4mod))
            if ed_to_focus:
                ed_to_focus.focus()
            elif not self._modal:
                ed.focus()
            
            self._modal = None
            return (self._retval, vals)
           #def when_close

        if self._modal:
            pass;               log__('as modal'      ,__=(log4fun,_log4mod))
#           self._modal = True
            app.dlg_proc(self.did, app.DLG_SHOW_MODAL)
            return   when_close()
        # Nonmodal
        app.dlg_proc(self.did, app.DLG_PROP_SET
                    ,prop=dict(on_close=lambda idd, idc=0, data='':
                     when_close()))
        pass;                   log__('as nonmodal'      ,__=(log4fun,_log4mod))
#       self._modal = False
        app.dlg_proc(self.did, app.DLG_SHOW_NONMODAL)
        self.activate()
        return (None, None)
       #def show

    ###############
    ## Getters
    ###############
    def focused(self, live=True):
        if not live:    return self.form.get('fid')
        form    = _dlg_proc(self.did, app.DLG_PROP_GET)
        c_ind   = form.get('focused')
        c_pr    = _dlg_proc(self.did, app.DLG_CTL_PROP_GET, index=c_ind)
        return c_pr['name']     if c_pr else None
       #def focused
    
    def fattr(self, attr, defv=None, live=True):
        """ Return one form property """
        if attr in ('focused', 'fid'):  return self.focused(live)
        pr  = _dlg_proc(self.did, app.DLG_PROP_GET) if live else    self.form
        return pr.get(attr, defv)
       #def fattr

    def fattrs(self, attrs=None, live=True):
        """ Return form properties """
        pr  = _dlg_proc(self.did, app.DLG_PROP_GET) if live else    self.form
        return pr      if not attrs else \
               {attr:(self.focused(live) if attr in ('focused', 'fid') else pr.get(attr)) 
                    for attr in attrs}
       #def fattrs

    def _cattr(self, lpr, cid, attr, attr_=None, defv=None):
        attr_   = attr_ if attr_ else _ATTR_TP_ABBRS.get(attr, attr)
        pass;                  #log("cid, attr, attr_={}",(cid, attr, attr_))
        pass;                  #log("lpr={}",(lpr))
        if attr  not in lpr and \
           attr_ not in lpr and \
           attr  not in _LIVE_CALC_ATTRS:                       # Only into mem
            mpr     = self.ctrls[cid]
            if attr  in mpr: return mpr[attr ]
            if attr_ in mpr: return mpr[attr_]
            pass;              #log("cid, defv={}",(cid,defv))
            return defv
        if attr=='r':
            return lpr['x'] + lpr['w']
        if attr=='b':
            return lpr['y'] + lpr['h']
        rsp     = lpr.get(attr, lpr.get(attr_, defv))
        if attr=='val' and rsp:
            return self._take_val( cid       , rsp, defv)
        if attr in ('cols_ws'): pass                            # See cattr/cattrs
        if attr in ('items', 'columns', 'cols') and rsp:
            return self._take_it_cl(cid, attr, rsp, defv)
        pass;                  #log("name, rsp={}",(name, rsp))
        return rsp
       #def _cattr

    def cattr(self, name, attr, defv=None, live=True):
        """ Return the attribute of the control.
            If no the attribute return defv.
            Take attribute value from screen (live) or from last settings (not live).
        """
        if name not in self.ctrls:  raise ValueError(f('Unknown name: {}', name))
        if attr=='cols_ws':
            return self._cols_serv('get-ws', name, live=live)
        attr_   = _ATTR_TP_ABBRS.get(attr, attr)
        mpr     = self.ctrls[name]
        if not live:
            return mpr.get(attr, mpr.get(attr_, defv))
        else:# live:
            # Some attrs not changable - return mem-value (if is)
            if attr  not in _LIVE_ATTRS and attr  in mpr:   return mpr[attr ]
            if attr_ not in _LIVE_ATTRS and attr_ in mpr:   return mpr[attr_]

        lpr     = _dlg_proc(self.did, app.DLG_CTL_PROP_GET, name=name)
        rsp     = self._cattr(lpr, name, attr, attr_)
        return rsp
       #def cattr

    def cattrs(self, name, attrs=None, live=True):
        """ Return the control attributes """
        pass;                   log4fun=1                       # Order log in the function
        if name not in self.ctrls:  raise ValueError(f('Unknown name: {}', name))
        mpr     = self.ctrls[name]
        if not live:
            attrs   = attrs if attrs else mpr
            return  odct([(attr
                          ,self.cattr(name, attr, live=live) if attr=='cols_ws' else 
                           mpr.get(attr)
                          ) 
                            for attr in attrs
                         ])
        elif attrs:# and live
            # Are all attrs not changable? - return mem-values (if is)
            rsp_attrs   = {}
            for attr in attrs:
                attr_   = _ATTR_TP_ABBRS.get(attr, attr)
                if   attr  not in _LIVE_ATTRS and attr  in mpr:
                    rsp_attrs[attr ]    = attr
                elif attr_ not in _LIVE_ATTRS and attr_ in mpr:
                    rsp_attrs[attr ]    = attr_
                else:
                    rsp_attrs   = None
                    break#for
            pass;              #log("rsp_attrs={}",(rsp_attrs))
            if rsp_attrs:
                return odct([(attr, mpr.get(rsp_attrs[attr])) for attr in rsp_attrs])
        
        lpr     = _dlg_proc(self.did, app.DLG_CTL_PROP_GET, name=name)
        attrs   = attrs if attrs else list(lpr.keys())
        return      odct([(attr
                          ,self.cattr(name, attr, live=live) if attr=='cols_ws' else 
                           self._cattr(lpr, name, attr)
                          )
                            for attr in attrs
                         ])
       #def cattrs
       
    def val(self, name, live=True):
        """ Return the control val property """
        return      self.cattr(name, 'val', defv=None, live=live)
    def vals(self, names=None, live=True):
        """ Return val property for the controls 
            or (if names==None) for all controls with val
        """
        names   = names \
                    if names else \
                  [cid  for (cid,cfg) in self.ctrls.items() 
                        if cfg['type'] in _TYPE_WITH_VALUE]
        return  odct([(cid, self.cattr(cid, 'val', defv=None, live=live))
                        for cid in names])
    

    ###############
    ## Updaters
    ###############
    def reset(self, ctrls, form, vals=None, fid=None, opts=None):
        pass;                   log4fun=0                       # Order log in the function
        _form_acts('save', did=self.did
                  ,key4store=self.opts.get('form data key'))
        app.dlg_proc(self.did, app.DLG_CTL_DELETE_ALL)
        
        self.opts   = opts.copy() if opts else {}
        self._setup(ctrls, form, vals, fid)
        return []
       #def reset
    
    def update(self, upds, retval=None, opts=None):
        """ Update most of dlg props
                upds        dict(ctrls=, form=, vals=, fid=) 
                    ctrls   [(name, {k:v})] or {name:{k:v}}
                    form    {k:v}
                    vals    {name:v}
                    fid     name
                            Or list of such dicts
                retval      Value to "show()" return if form will be hidden during the update
        """
        pass;                   log4fun=0                       # Order log in the function
        pass;                   log__("upds, retval, opts={}",(upds, retval, opts)      ,__=(log4fun,_log4mod))
#       if self._hidden:
#           pass;               log__('skip as hidden'      ,__=(log4fun,_log4mod))
#           return 
        if upds is None:                                        # To hide/close
            pass;              #log__('to hide'      ,__=(log4fun,_log4mod))
            if retval is not None and self._retval is None:
                self._retval = retval
            if  self._skip_free:
                self._skip_free = False
                return 
            app.dlg_proc(self.did, app.DLG_HIDE)
            self._hidden = True
            return
        if upds is False:
            pass;              #log__('to stop ev'      ,__=(log4fun,_log4mod))
            return False                                        # False to cancel the current event
        if likeslist(upds):                                     # Allow to use list of upd data
            pass;              #log__('many upds'      ,__=(log4fun,_log4mod))
            shown   = not self._hidden
            for upd in upds:
                self.update(upd, retval, opts=opts)
                if shown and self._hidden:    break             # hide is called on update
            return
        cupds   = upds.get('ctrls',  [])
        cupds   = odct(cupds)       if likeslist(cupds)                                     else cupds
        pass;                   log__('cupds={}',(cupds)      ,__=(log4fun,_log4mod))
        vals    = upds.get('vals', {})
        form    = upds.get('form', {})

        DlgAg._check_data(self.ctrls, cupds, form, vals, upds.get('fid'))

        if False:pass
        elif vals and not cupds:                                # Allow to update only val in some controls
            cupds     = { cid_    :  {'val':val} for cid_, val in vals.items()}
            pass;              #log("+vals-cupds cupds={}",(cupds))
        elif vals and     cupds:
            for cid_, val in vals.items():
                if cid_ not in cupds:
                    cupds[cid_]   =  {'val':val}                # Merge vals to cupds
                else:
                    cupds[cid_]['val']    = val                 # NB! Prefer val from vals but not from cupds
        for cid_, cfg in cupds.items():
            cfg['tp']   = self.ctrls[cid_]['tp']                # Type is stable
            cfg['type'] = self.ctrls[cid_]['type']              # Type is stable

        skip_form_upd   = opts and opts.get('_skip_form_upd' , False)
        skip_ctrls_upd  = opts and opts.get('_skip_ctrls_upd', False)
        if form:
            self.form.update(form)      if not skip_form_upd else 0
            pass;              #log('form={}',(self.fattrs(live=F)))
            pass;              #log('form={}',(self.fattrs()))
            pass;              #log('form={}',(form))
            _dlg_proc(self.did, app.DLG_PROP_SET
                     ,prop=form)

        if cupds:
            for cid, new_cfg in cupds.items():
                pass;          #log__('cid, new_cfg={}',(cid, new_cfg)      ,__=(log4fun,_log4mod))
                
                cfg     = self.ctrls[cid]
                pass;          #log__('cfg={}',(cfg)      ,__=(log4fun,_log4mod))
                cfg.update(new_cfg)     if not skip_ctrls_upd else 0
                pass;          #log__('cfg={}',(cfg)      ,__=(log4fun,_log4mod))
                c_prop  = self._prepare_control_prop(cid, new_cfg, {'ctrls':cupds})
                pass;          #log('c_prop={}',(c_prop)) if new_ctrl['type']=='listview' else None
                pass;           log__('c_prop={}',(c_prop)      ,__=(log4fun,_log4mod))
                _dlg_proc(self.did, app.DLG_CTL_PROP_SET
                         ,name=cid
                         ,prop=c_prop
                         )

        if 'fid' in upds or 'fid' in form:
            fid             = upds.get('fid', form.get('fid'))
            self.form['fid']= fid
            app.dlg_proc(self.did, app.DLG_CTL_FOCUS
                        ,name=fid)
       #def update
       
    @staticmethod
    def _check_data(mem_ctrls, ctrls, form, vals, fid):
        # Check cid/tid/fid in (ctrls, form, vals, fid) to exist into mem_ctrls
        if 'skip checks'!='skip checks':    return
        
        if likeslist(ctrls):
            cids    = [cid_cnt[0] for cid_cnt in ctrls]
            cids_d  = [cid for cid in cids if cids.count(cid)>1]
            if cids_d:
                raise ValueError(f('Repeated names: {}', set(cids_d)))
        
        no_tids = {cnt['tid'] 
                    for cnt in ctrls 
                    if 'tid' in cnt and 
                        cnt['tid'] not in mem_ctrls}
        if no_tids:
            raise ValueError(f('No name for tid: {}', no_tids))

        if 'fid' in form and form['fid'] not in mem_ctrls:
            raise ValueError(f('No name for form[fid]: {}', form['fid']))
        
        no_vals = {cid 
                    for cid in vals 
                    if cid not in mem_ctrls} if vals else None
        if no_vals:
            raise ValueError(f('No name for val: {}', no_vals))
        
        if fid is not None and fid not in mem_ctrls:
            raise ValueError(f('No name for fid: {}', fid))
       #def _check_data
       
    def _setup(self, ctrls, form, vals=None, fid=None):
        """ Arrange and fill all: controls attrs, form attrs, focus.
            Params
                ctrls   [(name, {k:v})] or {name:{k:v}} 
                            NB! Only from 5.7 Python saves key sequence for dict.
                                The sequence is important for tab-order of controls.
                form    {k:v}
                vals    {name:v}
                fid     name
        """
        pass;                   log4fun=0                       # Order log in the function
        #NOTE: DlgAg init
        self.ctrls  = odct(ctrls)   if likeslist(ctrls)                                     else ctrls.copy()
        self.form   = form.copy()
        fid         = fid           if fid else form.get('fid', form.get('focused'))    # focused?
        
        DlgAg._check_data(self.ctrls, ctrls, form, vals, fid)
        
        if vals:
            for cid, val in vals.items():
                self.ctrls[cid]['val']  = val
        
        # Create controls
        for cid, ccfg in self.ctrls.items():
            tp      = ccfg.get('tp',  ccfg.get('type'))
            if not tp:
                raise ValueError(f('No type/tp for name: {}', cid))
            ccfg['tp']      = tp
            ccfg['type']    = _TYPE_ABBRS.get(tp, tp)
            pass;              #log("tp,type={}",(tp,ccfg['type']))
            # Create control
            _dlg_proc(self.did, DLG_CTL_ADD_SET
                     ,name=ccfg['type']
                     ,prop=self._prepare_control_prop(cid, ccfg))
           #for cid, ccfg
        
        # Prepare form
        fpr             = self.form
        fpr['topmost']  = True
        wait_resize     = 'auto_stretch_col' in self.opts       # Agent will stretch column(s)
        # Prepare callbacks
        def get_proxy_cb(u_callbk, event):
            def form_callbk(idd, key=-1, data=''):
                pass;          #log("event,wait_resize={}",(event,wait_resize))
                if wait_resize and event=='on_resize':
                    self.update(self._on_resize()
                               ,opts={'_skip_ctrls_upd':True})  # Agent acts: stretch column(s), ...
                self._skip_free = (event=='on_resize')          # Ban to close dlg by some events (on_resize,...)
                upds    = u_callbk(self, key, data)
                if event=='on_close_query':                     # No upd, only bool about form close
                    return upds
                return self.update(upds)
            return form_callbk
            
        if wait_resize and 'on_resize' not in fpr:
            fpr['on_resize']    = lambda ag,k,d:[]              # Empty user callback
        for on_key in [k for k in fpr if k[:3]=='on_' and callable(fpr[k])]:
            fpr[on_key] = get_proxy_cb(fpr[on_key], on_key)
        
        self._prepare_anchors()                                 # a,aid -> a_*,sp_*
        for cid in self.opts.get('store_col_widths', []):
            self._cols_serv('restore-ws', cid=cid)
        self._prepare_frame()                                   # frame, border, on_resize
        
        if fid:
            fpr['fid']  = fid                                   # Save in mem
            app.dlg_proc(self.did, app.DLG_CTL_FOCUS, name=fid) # Push to live
       #def _setup

    def _on_resize(self):
        pass;                  #log("",())
        cupd    = {}
        if 'auto_stretch_col' in self.opts:
            for cid, stch in self.opts['auto_stretch_col'].items():
                if cid not in self.ctrls:   continue
                ctrl_w      = self.cattr(cid, 'w')
                if cid in self.opts.get('auto_start_col_width_on_min', []) and \
                   ctrl_w==self.cattr(cid, 'w', live=False):
                    # Min width - restore mem col width
                    col_ws      = self.cattr(cid, 'cols_ws', live=False)
                    pass;      #log("mem ws={}",(col_ws))
                else:
                    cols        = self.cattr(cid, 'cols', live=False)
                    cols        = cols      if cols else self.cattr(cid, 'cols')
                    min_cw      = cols[stch].get('mi', 20)
                    min_cw      = min_cw    if min_cw else 20
                    col_ws      = self.cattr(cid, 'cols_ws')
                    extra       = ctrl_w - len(col_ws) - SCROLL_W - sum(col_ws)
                    pass;      #log("w,SCROLL_W,extra,stch,ws[stch]={}",(ctrl_w,SCROLL_W,extra,stch,col_ws[stch]))
                    col_ws[stch]= max(min_cw, col_ws[stch] + extra)
                    pass;      #log("calc ws={}",(col_ws))
                cupd[cid]   = dict(cols_ws=col_ws)
                pass;          #log("ws={}",(col_ws))
        pass;                  #log("cupd={}",(cupd))
        return {'ctrls':cupd} if cupd else []
       #def _on_resize

    def _prepare_frame(self, fpr=None):
        fpr     = self.form if fpr is None else fpr
        w0,h0   = fpr['w'],fpr['h']
        pass;                  #log("fpr['on_resize']={}",(fpr['on_resize']))

        if callable(fpr.get('on_resize')) and 'resize' not in fpr.get('frame', ''):
            fpr['frame']    = fpr.get('frame', '') + 'resize'

        if False:pass
        elif 'frame' not in fpr and 'border' not in fpr:
            fpr['border']   = app.DBORDER_DIALOG
        elif 'border' in fpr:
            pass
        elif 'no' in fpr['frame']:
            fpr['border']   = app.DBORDER_NONE
        elif 'resize' in fpr['frame'] and ('full-cap' in fpr['frame'] or 'min-max' in fpr['frame']):
            fpr['border']   = app.DBORDER_SIZE
        elif 'resize' in fpr['frame']:
            fpr['border']   = app.DBORDER_TOOLSIZE
        elif 'full-cap' in fpr['frame'] or 'min-max' in fpr['frame']:
            fpr['border']   = app.DBORDER_SINGLE
        pass;                  #log("fpr['border']={}",(fpr['border'], get_const_name(fpr['border'], 'DBORDER_')))
        
        if fpr.get('border') in (app.DBORDER_SIZE, app.DBORDER_TOOLSIZE):
            fpr['w_min']    = fpr.get('w_min', w0)
            fpr['h_min']    = fpr.get('h_min', h0)
            fpr.pop('resize', None)
        
        # Restore prev pos/sizes
        fpr     = _form_acts('move', fprs=fpr                   # Move and (maybe) resize
                            , key4store=self.opts.get('form data key'))
        pass;                  #log("fpr['on_resize']={}",(fpr['on_resize']))
        pass;                  #log("fpr={}",(fpr))
        if      'on_resize' in fpr and (fpr['w'],fpr['h']) != (w0,h0):
            pass;              #log("fpr['on_resize']={}",(fpr['on_resize']))
            def on_show(idd,idc='',data=''):
                self.form['on_resize'](self)
                return []
            fpr['on_show']  = on_show
        _dlg_proc(self.did, app.DLG_PROP_SET, prop=fpr.copy())         # Push to live
       #def _prepare_frame

    def _prepare_control_prop(self, cid, ccfg, opts={}):
        pass;                   log4fun=0                       # Order log in the function
        Self    = self.__class__
        pass;                   log__('cid, ccfg={}',(cid, ccfg)      ,__=(log4fun,_log4mod))
        EXTRA_C_ATTRS   = ['tp','r','b','tid','a','aid']
        tp      = ccfg['type']
        pass;                   log__('cid, ccfg={}',(cid, ccfg)      ,__=(log4fun,_log4mod))
        Self._preprocessor(ccfg, tp)                            # sto -> tab_stop,...   EXTRA_C_ATTRS
        pass;                   log__('cid, ccfg={}',(cid, ccfg)      ,__=(log4fun,_log4mod))
        c_pr    = {k:v for (k,v) in ccfg.items()
                    if k not in ['items', 'val', 'columns', 'cols', 'cols_ws']
                               +EXTRA_C_ATTRS and 
                       (k[:3]!='on_' or k=='on')}
        c_pr['name'] = cid
        pass;                   log__('cid, ccfg={}',(cid, ccfg)      ,__=(log4fun,_log4mod))
        c_pr    = self._prepare_vl_it_cl(c_pr, ccfg, cid, opts) #if k     in ['items', 'val', 'cols']
        
        c_pr.update(
            self._prep_pos_attrs(ccfg, cid, opts.get('ctrls'))  # r,b,tid -> x,y,w,h
        ) 
        pass;                   log__('c_pr={}',(c_pr)      ,__=(log4fun,_log4mod))
        # Remove deprecated
        for attr in ('props',):
            c_pr.pop(attr, None)
        
        if self._c2m and 'hint' in c_pr:
            c_pr['hint']    = c_pr['hint'].replace('Ctrl+', 'Meta+')
        
        # Prepare callbacks
        def get_proxy_cb(u_callbk, event):
            def ctrl_callbk(idd, idc, data):
                pass;          #log('ev,idc,cid,data={}',(event,idc,cid,data))
#               if tp in ('listview',) and type(data) in (tuple, list):
                if tp in ('listview',) and likeslist(data):
                    if not data[1]: return                      # Skip event "selection loss"
                    # Crutch for Linux! Wait fix in core
                    event_val   = app.dlg_proc(idd, app.DLG_CTL_PROP_GET, index=idc)['val']
                    if event_val!=data[0]:
                        app.dlg_proc(          idd, app.DLG_CTL_PROP_SET, index=idc, prop={'val':data[0]})
                upds    = u_callbk(self, cid, data)
                return self.update(upds, cid)
               #def ctrl_callbk
            return ctrl_callbk
           #def get_proxy_cb
            
        for on_key in [k for k in ccfg if k[:3]=='on_' and callable(ccfg[k])]:
            if tp!='button':
                c_pr['act'] = True
            c_pr[on_key]    = get_proxy_cb(ccfg[on_key], on_key)
           #for on_key
        
        return c_pr
       #def _prepare_control_prop

    def _prep_pos_attrs(self, cnt, cid, ctrls4cid=None):
        pass;                   log4fun=0                       # Order log in the function
        ctrls4cid = ctrls4cid if ctrls4cid else self.ctrls
        reflect  = self.opts.get('negative_coords_reflect', False)
        pass;                   log__('cid, reflect, cnt={}',(cid, reflect, cnt)      ,__=(log4fun,_log4mod))
        prP     =  {}

        cnt_ty  = ctrls4cid[cid].get('tp', ctrls4cid[cid].get('type'))
        cnt_ty  = _TYPE_ABBRS.get(cnt_ty, cnt_ty)
        if  cnt_ty in ('label', 'linklabel'
                      ,'combo', 'combo_ro'
                      )         \
        or  'h' not in cnt  and \
            cnt_ty in ('button', 'checkbutton'
                      ,'edit', 'spinedit'
                      ,'check', 'radio'
                      ,'filter_listbox', 'filter_listview'
                      ):
            # OS specific control height
            cnt['h']    = _get_gui_height(cnt_ty)               # Some types kill 'h'
            prP['_ready_h'] = True                              # Skip scaling
            pass;              #log('cnt={}',(cnt)) if cnt_ty=='checkbutton' else 0

        if 'tid' in cnt:
            assert cnt['tid'] in ctrls4cid
            # cid for horz-align text
            bas_cnt     = ctrls4cid[ cnt['tid']]
            bas_ty      = bas_cnt.get('tp', bas_cnt.get('type'))
            bas_ty      = _TYPE_ABBRS.get(bas_ty, bas_ty)
            t           = bas_cnt.get('y', 0) + _fit_top_by_env(cnt_ty, bas_ty)
            cnt['y']    = t                                     # 'tid' kills 'y'
        
        if reflect: #NOTE: reflect
            def do_reflect(cnt_, k, pval):
                if 0>cnt_.get(k, 0):
                    pass;       log__('cid, k, pval, cnt_={}',(cid, k, pval, cnt_)      ,__=(log4fun,_log4mod))
                    cnt_[k]    = pval + cnt_[k]
                    pass;       log__('cnt_={}',(cnt_)      ,__=(log4fun,_log4mod))
            prnt    = cnt.get('p', self.form)
            prnt_w  = prnt.get('w', 0) 
            prnt_h  = prnt.get('h', 0)
            pass;               log__('prnt={}',(prnt)      ,__=(log4fun,_log4mod))
            pass;               log__('prnt_w,prnt_h={}',(prnt_w,prnt_h)      ,__=(log4fun,_log4mod))
            pass;               log__('cnt={}',(cnt)      ,__=(log4fun,_log4mod))
            do_reflect(cnt, 'x', prnt_w)
            do_reflect(cnt, 'r', prnt_w)
            do_reflect(cnt, 'y', prnt_h)
            do_reflect(cnt, 'b', prnt_h)
            pass;               log__('cnt={}',(cnt)      ,__=(log4fun,_log4mod))

        def calt_third(kasx, kasr, kasw, src, trg):
            # Use d[kasw] = d[kasr] - d[kasx]
            #   to copy val from src to trg
            # Skip kasr if it is redundant
            if False:pass
            elif kasx in src and kasw in src:                   # x,w or y,h is enough
                trg[kasx]   = src[kasx]
                trg[kasw]   = src[kasw]
            elif kasr in src and kasw in src:                   # r,w or b,h to calc
                trg[kasx]   = src[kasw] - src[kasr]
                trg[kasw]   = src[kasw]
            elif kasx in src and kasr in src:                   # x,r or y,b to calc
                trg[kasx]   = src[kasx]
                trg[kasw]   = src[kasr] - src[kasx]
            return trg
           #def calt_third
        
        prP = calt_third('x', 'r', 'w', cnt, prP)
        prP = calt_third('y', 'b', 'h', cnt, prP)
        pass;                  #log__('cid, prP={}',(cid, prP)      ,__=(log4fun,_log4mod))
        return prP
       #def _prep_pos_attrs

    def _prepare_vl_it_cl(self, c_pr, cfg_ctrl, cid, opts={}):
        pass;                   log4fun=0                       # Order log in the function
        pass;                   log__('c_pr={}',(c_pr)      ,__=(log4fun,_log4mod))
        pass;                   log__('cfg_ctrl={}',(cfg_ctrl)      ,__=(log4fun,_log4mod))
        pass;                   log__('opts={}',(opts)      ,__=(log4fun,_log4mod))
        tp      = cfg_ctrl['type']

        if 'val' in cfg_ctrl        and opts.get('prepare val', True):
            in_val  = cfg_ctrl['val']
            def list_to_list01(lst):
                return list(('1' if v=='1' or v is True else '0') 
                            for v in lst)
            if False:pass
            elif tp=='memo':
                # For memo: "\t"-separated lines (in lines "\t" must be replaced to chr(3)) 
                pass;           log__("tp,in_val={}",(tp,in_val)      ,__=(log4fun,_log4mod))
                if likeslist(in_val):
                    in_val = '\t'.join([v.replace('\t', chr(3)) for v in in_val])
                else:
                    in_val = in_val.replace('\t', chr(3)).replace('\r\n','\n').replace('\r','\n').replace('\n','\t')
                pass;           log__("tp,in_val={}",(tp,in_val)      ,__=(log4fun,_log4mod))
            elif tp=='checkgroup' and likeslist(in_val):
                # For checkgroup: ","-separated checks (values "0"/"1") 
                in_val = ','.join(list_to_list01(in_val))
            elif tp in ['checklistbox', 'checklistview'] and likeslist(in_val):
                # For checklistbox, checklistview: index+";"+checks 
                in_val = ';'.join( (str(in_val[0]), ','.join(list_to_list01(in_val[1])) ) )
            c_pr['val']     = in_val

        if 'items' in cfg_ctrl        and opts.get('prepare items', True):
            items   = cfg_ctrl['items']
            pass;               log__("tp,items={}",(tp,items)      ,__=(log4fun,_log4mod))
            if likesstr(items):
                pass
            elif tp in ['listview', 'checklistview']:
                # For listview, checklistview: "\t"-separated items.
                #   first item is column headers: title1+"="+size1 + "\r" + title2+"="+size2 + "\r" +...
                #   other items are data: cell1+"\r"+cell2+"\r"+...
                # ([(hd,wd)], [[cells],[cells],])
                items   = '\t'.join(['\r'.join(['='.join((hd,str(sz))) for hd,sz in items[0]])]
                                   +['\r'.join(row) for row in items[1]]
                                   )
            else:
                # For combo, combo_ro, listbox, checkgroup, radiogroup, checklistbox: "\t"-separated lines
                items   = '\t'.join(items)
            pass;               log__("items={}",(items)      ,__=(log4fun,_log4mod))
            c_pr['items']   = items

        if ('cols' in cfg_ctrl or 'columns' in cfg_ctrl or 'cols_ws' in cfg_ctrl)   and opts.get('prepare cols', True):
            cols    = cfg_ctrl.get('cols', cfg_ctrl.get('columns'))
            cols    = cols if cols else self.cattr(cid, 'cols')
            cfg_ctrl['columns'] = cols
            if likesstr(cols):
                pass
            else:
                if 'cols_ws' in cfg_ctrl:
                    cols_ws  = cfg_ctrl['cols_ws']
                    pass;      #log("cols_ws={}",(cols_ws))
                    if len(cols_ws)!=len(cols): raise ValueError(f('Inconsistent attribures: cols/columns and cols_ws'))
                    for n,w in enumerate(cols_ws):
                        cols[n]['wd']   = w
                # For listview, checklistview: 
                #   "\t"-separated of 
                #       "\r"-separated 
                #           Name, Width, Min Width, Max Width, Alignment (str), Autosize('0'/'1'), Visible('0'/'1')
                pass;          #log('cols={}',(cols))
                str_sc = lambda n: str(_os_scale('scale', {'w':n})['w'])
                cols   = '\t'.join(['\r'.join([       cd[    'hd']
                                              ,str_sc(cd.get('wd' ,0))
                                              ,str_sc(cd.get('mi' ,0))
                                              ,str_sc(cd.get('ma' ,0))
                                              ,       cd.get('al','')
                                              ,'1' if cd.get('au',False) else '0'
                                              ,'1' if cd.get('vi',True ) else '0'
                                              ])
                                    for cd in cols]
                                  )
                pass;          #log('cols={}',repr(cols))
            c_pr['columns'] = cols

        return c_pr
       #def _prepare_vl_it_cl

    def _take_val(self, name, liv_val, defv=None):
        pass;                   log4fun=0                       # Order log in the function
        pass;                   log__("name, liv_val={}",(name, liv_val)      ,__=(log4fun,_log4mod))
        tp      = self.ctrls[name]['type']
        old_val = self.ctrls[name].get('val', defv)
        new_val = liv_val
        if False:pass
        elif tp=='memo':
            # For memo: "\t"-separated lines (in lines "\t" must be replaced to chr(3)) 
            if likeslist(old_val):
#               new_val = [v.replace(chr(3), '\t') for v in liv_val.split('\t')]
                new_val = [v.replace(chr(2), '\t')              ##!! Wait core fix
                            .replace(chr(3), '\t') for v in liv_val.split('\t')]
               #liv_val = '\t'.join([v.replace('\t', chr(3)) for v in old_val])
            else:
                new_val = liv_val.replace('\t','\n').replace(chr(3), '\t')
               #liv_val = old_val.replace('\t', chr(3)).replace('\r\n','\n').replace('\r','\n').replace('\n','\t')
        elif tp=='checkgroup' and likeslist(old_val):
            # For checkgroup: ","-separated checks (values "0"/"1") 
            new_val = liv_val.split(',')
           #in_val = ','.join(in_val)
        elif tp in ['checklistbox', 'checklistview'] and likeslist(old_val):
            new_val = liv_val.split(';')
            new_val = (new_val[0], new_val[1].split(','))
           #liv_val = ';'.join(old_val[0], ','.join(old_val[1]))
        elif isinstance(old_val, bool): 
            new_val = liv_val=='1'
        elif tp=='listview':
            new_val = -1 if liv_val=='' else int(liv_val)
        elif old_val is not None: 
            pass;              #log('name,old_val,liv_val={}',(name,old_val,liv_val))
            new_val = type(old_val)(liv_val)
        return new_val
       #def _take_val

    def _take_it_cl(self, cid, attr, liv_val, defv=None):
        tp      = self.ctrls[cid]['type']
        old_val = self.ctrls[cid].get(attr, defv)
        pass;                  #log('cid, attr, isinstance(old_val, str)={}',(cid, attr, isinstance(old_val, str)))
        if likesstr(old_val):
            # No need parsing - config was by string
            return liv_val
        new_val = liv_val
        
        if attr=='items':
            if tp in ['listview', 'checklistview']:
                # For listview, checklistview: "\t"-separated items.
                #   first item is column headers: title1+"="+size1 + "\r" + title2+"="+size2 + "\r" +...
                #   other items are data: cell1+"\r"+cell2+"\r"+...
                # ([(hd,wd)], [[cells],[cells],])
                header_rows = new_val.split('\t')
                new_val =[[h.split('=')  for h in header_rows[0].split('\r')]
                         ,[r.split('\r') for r in header_rows[1:]]
                         ]
            else:
                # For combo, combo_ro, listbox, checkgroup, radiogroup, checklistbox: "\t"-separated lines
                new_val     = new_val.split('\t')
        
        if attr in ('columns', 'cols'):
            # For listview, checklistview: 
            #   "\t"-separated of 
            #       "\r"-separated 
            #           Name, Width, Min Width, Max Width, Alignment (str), Autosize('0'/'1'), Visible('0'/'1')
            # [{nm:str, wd:num, mi:num, ma:num, al:str, au:bool, vi:bool}]
            pass;              #log('new_val={}',repr(new_val))
            new_val= [ci.split('\r')      for ci in new_val.split('\t')]
            pass;              #log('new_val={}',repr(new_val))
            int_sc = lambda s: _os_scale('unscale', {'w':int(s)})['w']
            new_val= [odct(('hd',       ci[0])
                          ,('wd',int_sc(ci[1]))
                          ,('mi',int_sc(ci[2]))
                          ,('ma',int_sc(ci[3]))
                          ,('al',       ci[4])
                          ,('au','1'==  ci[5])
                          ,('vi','1'==  ci[6])
                          ) for ci in new_val]
            pass;              #log('new_val={}',(new_val))
        
        return new_val
       #def _take_it_cl

    @staticmethod
    def _preprocessor(cnt, tp):
        pass;                   log4fun=0                       # Order log in the function
        pass;                   log__('tp,cnt={}',(tp,cnt)      ,__=(log4fun,_log4mod))
        # on -> on_???
        if 'on' in cnt:
            if False:pass
            elif tp in ('listview', 'treeview'):
                cnt['on_select']    = cnt['on']
            elif tp in ('linklabel'):
                cnt['on_click']     = cnt['on']
            else:
                cnt['on_change']    = cnt['on']

        # Joins
        if 'sp_lr' in cnt:
            cnt['sp_l'] = cnt['sp_r']               = cnt['sp_lr']
        if 'sp_lrt' in cnt:
            cnt['sp_l'] = cnt['sp_r'] = cnt['sp_t'] = cnt['sp_lrt']
        if 'sp_lrb' in cnt:
            cnt['sp_l'] = cnt['sp_r'] = cnt['sp_b'] = cnt['sp_lrb']

        cnt['autosize'] = False
        # Abbreviations
        for attr in _ATTR_ABBRS:
            if attr in cnt:
                cnt[_ATTR_ABBRS[attr]] = cnt[attr]                      # ali -> align, au -> autosize, ...
        pass;                  #log__('tp,cnt={}',(tp,cnt)      ,__=(log4fun,_log4mod))
        # Copy smth to props
        if 'props' in cnt:
            pass
        elif tp=='label' and cnt.get('cap', '').startswith('>'):        # cap='>smth' -> cap='smth', props='1' (r-align)
            cnt['cap']  = cnt['cap'][1:]
            cnt['props']= '1'
        elif tp=='label' and    cnt.get('ralign'):                      # ralign -> props
            cnt['props']=           cnt['ralign']
        elif tp=='button' and cnt.get('def_bt') in ('1', True):         # def_bt -> props
            cnt['props']= '1'
        elif tp=='spinedit' and cnt.get('min_max_inc'):                 # min_max_inc -> props
            cnt['props']=           cnt['min_max_inc']
        elif tp=='linklabel' and    cnt.get('url'):                     # url -> props
            cnt['props']=               cnt['url']
        elif tp=='listview' and cnt.get('grid'):                        # grid -> props
            cnt['props']=       cnt['grid']
        elif tp=='tabs' and     cnt.get('at_botttom'):                  # at_botttom -> props
            cnt['props']=           cnt['at_botttom']
        elif tp=='colorpanel' and   cnt.get('brdW_fillC_fontC_brdC'):   # brdW_fillC_fontC_brdC -> props
            cnt['props']=               cnt['brdW_fillC_fontC_brdC']
        elif tp in ('edit', 'memo') and cnt.get('ro_mono_brd'):         # ro_mono_brd -> props
            cnt['props']=                   cnt['ro_mono_brd']

        # Convert props to ex0..ex9
        #   See 'Prop "ex"' at wiki.freepascal.org/CudaText_API
        lsPr = cnt.get('props', '')
        lsPr = lsPr if type(lsPr)==str else '1' if lsPr else '0'
        lsPr = lsPr.split(',')
        pass;                   log__('lsPr={}',(lsPr)      ,__=(log4fun,_log4mod))
        if False:pass
        elif tp=='button'       and 0<len(lsPr):
            cnt['ex0']  = '1'==lsPr[0]                      #bool: default for Enter key
        elif tp in ('edit', 'memo') \
                                and 2<len(lsPr):
            cnt['ex0']  = '1'==lsPr[0]                      #bool: read-only
            cnt['ex1']  = '1'==lsPr[1]                      #bool: font is monospaced
            cnt['ex2']  = '1'==lsPr[2]                      #bool: show border
        elif tp=='spinedit'     and 2<len(lsPr):
            cnt['ex0']  =  int(lsPr[0])                     #int:  min value
            cnt['ex1']  =  int(lsPr[1])                     #int:  max value
            cnt['ex2']  =  int(lsPr[2])                     #int:  increment
        elif tp=='label'        and 0<len(lsPr):
            cnt['ex0']  = '1'==lsPr[0]                      #bool: right aligned
        elif tp=='linklabel'    and 0<len(lsPr):
            cnt['ex0']  =      lsPr[0]                      #str: URL. Should not have ','. 
                                                            #     Clicking on http:/mailto: URLs should work, result of clicking on other kinds depends on OS.
        elif tp=='listview'     and 0<len(lsPr):
            cnt['ex0']  = '1'==lsPr[0]                      #bool: show grid lines
        elif tp=='tabs'         and 0<len(lsPr):
            cnt['ex0']  = '1'==lsPr[0]                      #bool: show tabs at bottom
        elif tp=='colorpanel'   and 3<len(lsPr):
            cnt['ex0']  =  int(lsPr[0])                     #int:  border width (from 0)
            cnt['ex1']  =  int(lsPr[1])                     #int:  color of fill
            cnt['ex2']  =  int(lsPr[2])                     #int:  color of font
            cnt['ex3']  =  int(lsPr[3])                     #int:  color of border
        elif tp=='filter_listview' \
                                and 0<len(lsPr):
            cnt['ex0']  = '1'==lsPr[0]                      #bool: filter works for all columns
        elif tp=='image'        and 5<len(lsPr):
            cnt['ex0']  = '1'==lsPr[0]                      #bool: center picture
            cnt['ex1']  = '1'==lsPr[1]                      #bool: stretch picture
            cnt['ex2']  = '1'==lsPr[2]                      #bool: allow stretch in
            cnt['ex3']  = '1'==lsPr[3]                      #bool: allow stretch out
            cnt['ex4']  = '1'==lsPr[4]                      #bool: keep origin x, when big picture clipped
            cnt['ex5']  = '1'==lsPr[5]                      #bool: keep origin y, when big picture clipped
        elif tp=='trackbar'     and 7<len(lsPr):
            cnt['ex0']  =  int(lsPr[0])                     #int:  orientation (0: horz, 1: vert)
            cnt['ex1']  =  int(lsPr[1])                     #int:  min value
            cnt['ex2']  =  int(lsPr[2])                     #int:  max value
            cnt['ex3']  =  int(lsPr[3])                     #int:  line size
            cnt['ex4']  =  int(lsPr[4])                     #int:  page size
            cnt['ex5']  = '1'==lsPr[5]                      #bool: reversed
            cnt['ex6']  =  int(lsPr[6])                     #int:  tick marks position 
                                                            #      (0: bottom-right, 1: top-left, 2: both)
            cnt['ex7']  =  int(lsPr[7])                     #int:  tick style 
                                                            #      (0: none, 1: auto, 2: manual)
        elif tp=='progressbar'  and 7<len(lsPr):
            cnt['ex0']  =  int(lsPr[0])                     #int:  orientation 
                                                            #      (0: horz, 1: vert, 2: right-to-left, 3: top-down)
            cnt['ex1']  =  int(lsPr[1])                     #int:  min value
            cnt['ex2']  =  int(lsPr[2])                     #int:  max value
            cnt['ex3']  = '1'==lsPr[3]                      #bool: smooth bar
            cnt['ex4']  =  int(lsPr[4])                     #int:  step
            cnt['ex5']  =  int(lsPr[5])                     #int:  style (0: normal, 1: marquee)
            cnt['ex6']  = '1'==lsPr[6]                      #bool: show text (only for some OSes)
        elif tp=='progressbar_ex' \
                                and 6<len(lsPr):
            cnt['ex0']  =  int(lsPr[0])                     #int:  style 
                                                            #      (0: text only
                                                            #      ,1: horz bar
                                                            #      ,2: vert bar
                                                            #      ,3: pie
                                                            #      ,4: needle
                                                            #      ,5: half-pie)
            cnt['ex1']  =  int(lsPr[1])                     #int:  min value
            cnt['ex2']  =  int(lsPr[2])                     #int:  max value
            cnt['ex3']  = '1'==lsPr[3]                      #bool: show text
            cnt['ex4']  =  int(lsPr[4])                     #int:  color of background
            cnt['ex5']  =  int(lsPr[5])                     #int:  color of foreground
            cnt['ex6']  =  int(lsPr[6])                     #int:  color of border
        elif tp=='bevel'        and 0<len(lsPr):
            cnt['ex0']  =  int(lsPr[0])                     #int:  shape 
                                                            #      (0: sunken panel
                                                            #      ,1: 4 separate lines - use it as border for group of controls
                                                            #      ,2: top line
                                                            #      ,3: bottom line
                                                            #      ,4: left line
                                                            #      ,5: right line
                                                            #      ,6: no lines, empty space)
        elif tp=='splitter'     and 3<len(lsPr):
            cnt['ex0']  = '1'==lsPr[0]                      #bool: beveled style
            cnt['ex1']  = '1'==lsPr[1]                      #bool: instant repainting
            cnt['ex2']  = '1'==lsPr[2]                      #bool: auto snap to edge
            cnt['ex3']  =  int(lsPr[3])                     #int:  min size

        pass;                   log__('cnt={}',(cnt)      ,__=(log4fun,_log4mod))
       #def _preprocessor

    def _prepare_anchors(self):
        """ Translate attrs 'a' 'aid' to 'a_*','sp_*'
            Values for 'a' are str-mask with signs
                'l<' 'l>'    fixed distanse ctrl-left     to trg-left  or trg-right
                'r<' 'r>'    fixed distanse ctrl-right    to trg-left  or trg-right
                't^' 't.'    fixed distanse ctrl-top      to trg-top   or trg-bottom
                'b^' 'b.'    fixed distanse ctrl-bottom   to trg-top   or trg-bottom
        """
        fm_w    = self.form['w']
        fm_h    = self.form['h']
        for cid,cnt in self.ctrls.items():
            anc     = cnt.get('a'  , '')
            if not anc: continue
            aid     = cnt.get('aid', cnt.get('p', ''))    # '' anchor to form
            trg_w,  \
            trg_h   = fm_w, fm_h
            if aid in self.ctrls:
                prTrg   = _dlg_proc(self.did, app.DLG_CTL_PROP_GET, name=aid)
                trg_w,  \
                trg_h   = prTrg['w'], prTrg['h']
            prOld   = _dlg_proc(self.did, app.DLG_CTL_PROP_GET, name=cid)
            pass;               logb=cid in ('tolx', 'tofi')
            pass;              #nat_prOld=app.dlg_proc(self.did, app.DLG_CTL_PROP_GET, name=cid)
            pass;              #log('cid,nat-prOld={}',(cid,{k:v for k,v in nat_prOld.items() if k in ('x','y','w','h','_ready_h')})) if logb else 0
            pass;              #log('cid,    prOld={}',(cid,{k:v for k,v in     prOld.items() if k in ('x','y','w','h','_ready_h')})) if logb else 0
            pass;              #log('cid,anc,trg_w,trg_h,prOld={}',(cid,anc,trg_w,trg_h, {k:v for k,v in prOld.items() if k in ('x','y','w','h')})) \
                               #    if logb else 0
            prAnc   = {}
            l2r     = 'l>' in anc or '>>' in anc
            r2r     = 'r>' in anc or '>>' in anc
            t2b     = 't.' in anc or '..' in anc
            b2b     = 'b.' in anc or '..' in anc
            if False:pass
            elif '--' in anc:           # h-center
                prAnc.update(dict( a_l=(aid, '-')
                                  ,a_r=(aid, '-')))
            elif not l2r and not r2r:   # Both to left
                pass # def
            elif     l2r and     r2r:   # Both to right
                pass;          #log('l> r>') if logb else 0
                prAnc.update(dict( a_l=None                                             # (aid, ']'), sp_l=trg_w-prOld['x']
                                  ,a_r=(aid, ']'), sp_r=trg_w-prOld['x']-prOld['w']))
            elif     l2r and not r2r:   # Left to right
                pass;          #log('l> r<') if logb else 0
                prAnc.update(dict( a_l=(aid, '['), sp_l=trg_w-prOld['x']
                                  ,a_r=None))
            elif not l2r and     r2r:   # Right to right.
                pass;          #log('l< r>') if logb else 0
                prAnc.update(dict( a_l=(aid, '['), sp_l=      prOld['x']
                                  ,a_r=(aid, ']'), sp_r=trg_w-prOld['x']-prOld['w']))
            
            if False:pass
            elif '||' in anc:           # v-center
                prAnc.update(dict( a_t=(aid, '-')
                                  ,a_b=(aid, '-')))
            elif not t2b and not b2b:   # Both to top
                pass # def
            elif     t2b and     b2b:   # Both to bottom
                pass;          #log('t. b.') if logb else 0
                prAnc.update(dict( a_t=None      #, sp_t=trg_h-prOld['y']                # a_t=(aid, ']') - API bug
                                  ,a_b=(aid, ']'), sp_b=trg_h-prOld['y']-prOld['h']))
            elif     t2b and not b2b:   # Top to bottom
                pass;          #log('t. b^') if logb else 0
                prAnc.update(dict( a_t=(aid, ']'), sp_t=trg_h-prOld['y']                # a_t=(aid, ']') - API bug
                                  ,a_b=None))
            elif not t2b and     b2b:   # Bottom to bottom.
                pass;          #log('t^ b.') if logb else 0
                prAnc.update(dict( a_t=(aid, '['), sp_t=      prOld['y']
                                  ,a_b=(aid, ']'), sp_b=trg_h-prOld['y']-prOld['h']))
            
            if prAnc:
                pass;          #log('aid,prAnc={}',(cid, prAnc)) if logb else 0
                cnt.update(prAnc)
                _dlg_proc(self.did, app.DLG_CTL_PROP_SET, name=cid, prop=prAnc)
#               pass;           pr_   = _dlg_proc(self.did, app.DLG_CTL_PROP_GET, name=cid)
#               pass;           log('cid,pr_={}',(cid, {k:v for k,v in pr_.items() if k in ('h','y', 'sp_t', 'sp_b', 'a_t', 'a_b')}))
       #def _prepare_anchors


    ###############
    ## Services
    ###############

    def _cols_serv(self, what, cid=None, live=True, data=None):
        pass;                   log4fun=0                       # Order log in the function
        pass;                   log__('what, cid, live, data={}',(what, cid, live, data)      ,__=(log4fun,_log4mod))

        if what=='get-ws':                                      # Return col widths [w1, w2, ...] for the control
            if live:
                cols    = self.cattr(cid, 'cols')
                return [ci['wd'] for ci in cols]    if cols else None
            cpr     = self.ctrls[cid]
            pass;              #log("cpr={}",(cpr))
            if 'cols_ws' in cpr:
                return cpr['cols_ws']
            cols    = cpr.get('cols', cpr.get('columns'))
            if cols and all('wd' in ci for ci in cols):
                return [ci['wd'] for ci in cols]
            items   = cpr['items']
            return [wd for hd,wd in items[0]]       if items else None

        COL_WS_SUFFIX   = '_col_widths'
        
        if what=='restore-ws':                                  # Set col widths for the control from hist
            fm_key  = _gen_form_key(self.form)
            ws      = get_hist([fm_key, cid+COL_WS_SUFFIX])
            if not ws:  return 
            pass;               log__('fm_key, ws={}',(fm_key, ws)      ,__=(log4fun,_log4mod))
            cols    = self.cattr(cid, 'cols')
            pass;              #log__('cols={}',(cols)      ,__=(log4fun,_log4mod))
            if len(ws)!=len(cols):  return 
            for n,w in enumerate(ws):
                cols[n]['wd']   = w
            self.update({'ctrls': {cid: {'cols':cols}}}, opts={'_skip_ctrls_upd':True})
            return 
        
        if what=='save-ws':                                     # Store live col widths for the control
            ws      = self._cols_serv('get-ws', cid)
            fm_key  = _gen_form_key(self.form)
            pass;               log__('fm_key, ws={}',(fm_key, ws)      ,__=(log4fun,_log4mod))
            set_hist([fm_key, cid+COL_WS_SUFFIX], ws)
            return 
       #def _cols_serv


    ###############
    ## Helpers
    ###############

    def scam(self):
        scam= app.app_proc(app.PROC_GET_KEYSTATE, '')
        scam= scam.replace('m', 'c') if self._c2m else scam
        return scam
    
    
    def hide(self, retval=None):
        """ Hide form
            retval      Value to "show()" return
        """
        if retval is not None and self._retval is None:
            self._retval = retval
        if  self._skip_free:
            self._skip_free = False
            return 
        if self._hidden:
            return 
        self._hidden = True
        return app.dlg_proc(self.did, app.DLG_HIDE)
    
    
    def activate(self):
        """ Set focus to the form """
        return app.dlg_proc(self.did, app.DLG_FOCUS)
    
    
    def dock(self, side='b', undock=False, ag_parent=None):
        """ [Un]Dock the form to the side of form/window.
            side        'l', 'r', 't', 'b' to dock to the side
                        '' to undock
            undock      Undock form (as side='')
            ag_parent   Other form agent, None - main app window
        """
        pass;                   log4fun=0
        undock  = undock if side        else True               # to use only side
        side    = side   if not undock  else ''                 # to use only side
        pass;                   log__("side, undock, ag_parent={}",(side, undock, ag_parent)      ,__=(log4fun,_log4mod))
        if side==self._dockto:
            pass;               log__("skip as already"      ,__=(log4fun,_log4mod))
            return 
        if side and self._modal is True:
            pass;               log__("skip as modal"      ,__=(log4fun,_log4mod))
            return 
        self._dockto= side
        if not side:
            app.dlg_proc(self.did, app.DLG_UNDOCK)
            if not self._hidden:
                fpr     = {k:v for k,v in self.form.items() if k in ('border', 'cap')}
                fpr     = _form_acts('move', fprs=fpr               # Move and (maybe) resize
                                    , key4store=self.opts.get('form data key'))
                _dlg_proc(self.did, app.DLG_PROP_SET, prop=fpr)     # Push to live
        else:
            if not self._hidden:
                _form_acts('save', did=self.did
                          ,key4store=self.opts.get('form data key'))
            side    = side.upper() if side in ('l', 'r', 't', 'b') else 'B'
            self.form['border'] = self.fattr('border')              # Save to use on undock
            app.dlg_proc(self.did, app.DLG_DOCK
                        ,index=(ag_parent.did if ag_parent else 0)
                        ,prop=side)
       #def dock
    
    
    def islived(self):
        return app.dlg_proc(self.did, app.DLG_PROP_GET) is not None
    
    
    def fhandle(self):
        return self.did
    
    
    def chandle(self, name):
        return app.dlg_proc(self.did, app.DLG_CTL_HANDLE, name=name)

    
    def show_menu(self, mn_content, name, where='+h', dx=0, dy=0, cmd4all=None, repro_to_file=None):
        """ mn_content      [{ cap:''
                             , tag:''
                             , en:T
                             , mark:''|'c'|'r'
                             , cmd:(lambda ag, tag:'')
                             , sub:[]}
                            ]
            name            Control to show menu near it
            where           Menu position 
                                '+h'    - under the control
                                '+w'    - righter the control
                                'dxdy'  - to use dx, dy 
            cmd4all         Handler for all nodes in mn_content
            repro_to_file   File name (w/o path) to write reprocode with only menu_proc 
        """
        if cmd4all:
            set_all_for_tree(mn_content, 'sub', 'cmd', cmd4all)       # All nodes have same cmd
        pr      = self.cattrs(name, ('x','y','w','h', 'p'))
        pid     = pr['p']
        while pid:
            ppr = self.cattrs(pid, ('x','y', 'p'))
            pass;              #log('pid, ppr={}',())
            pr['x']+= ppr['x']
            pr['y']+= ppr['y']
            pid     = ppr['p']
        x, y    =  pr['x']+(pr['w']         if '+w' in where else 0) \
                ,  pr['y']+(pr['h']         if '+h' in where else 0)
        x, y    = (pr['x']+dx, pr['y']+dy)  if where=='dxdy' else (x, y)
        pass;                  #log('(x, y), (dx, dy), pr={}',((x, y), (dx, dy), pr))
        prXY    = _os_scale('scale', {'x':x, 'y':y})
        x, y    = prXY['x'], prXY['y']
        pass;                  #log('x, y={}',(x, y))
        x, y    = app.dlg_proc(self.did, app.DLG_COORD_LOCAL_TO_SCREEN, index=x, index2=y)
        pass;                  #log('x, y={}',(x, y))
        
        return show_menu(mn_content, x, y, self, repro_to_file, opts=dict(c2m=self._c2m))
       #def show_menu

    def gen_repro_code(self, rtf=None):
        # Make repro-code has only core API calls
        pass;                   log4fun=0                       # Order  log in the function
        rtf     = self.opts.get('gen_repro_to_file', False) if rtf is None else rtf
        if not rtf: return 
        rerpo_fn= tempfile.gettempdir()+os.sep+(rtf if likesstr(rtf) else 'repro_dlg_proc.py')
        print(f(r'exec(open(r"{}", encoding="UTF-8").read())', rerpo_fn))

        l       = '\n'
        cattrs  = [  ('type', 'tag', 'act')
                    ,('name', 'x', 'y', 'w', 'h', 'w_min', 'h_min', 'w_max', 'h_max', 'cap', 'hint', 'p')
                    ,('en', 'vis', 'focused', 'tab_stop', 'tab_order'
                     ,'props', 'ex0', 'ex1', 'ex2', 'ex3', 'ex4', 'ex5', 'ex6', 'ex7', 'ex8', 'ex9'
                     ,'sp_l', 'sp_r', 'sp_t', 'sp_b', 'sp_a', 'a_l', 'a_r', 'a_t', 'a_b', 'align')
                    ,('val', 'items', 'columns')
                    ,('tp', 'b', 'r', 'tid', 'a', 'aid', 'def_bt')
                  ]
        fattrs  = [  ('x', 'y', 'w', 'h', 'cap', 'tag')
                    ,('border', 'w_min', 'w_max', 'h_min', 'h_max', 'topmost', 'focused')
                    ,('vis', 'keypreview')
                    ,('frame')
                  ]
        def out_attrs(pr, attrs, out=''):
            pr          = pr.copy()
            out         += '{'+l
            afix        = ''
            for ats in attrs:
                apr     =   {k:pr.pop(k) for k in ats if k in pr}
                if apr:
                    out += afix + ', '.join(repr(k) + ':' + repr(apr[k]) for k in ats if k in apr)
                    afix= '\n,'
            apr =           {k:pr.pop(k) for k in pr.copy() if k[0:3]!='on_'}
            if apr:
                out     += afix + repr(apr).strip('{}') 
            for k in pr:
                out     += afix + f('"{}":(lambda idd,idc,data:print("{}"))', k, k)
            out         += '}'
            return out
        srp     =    ''
        srp    +=    'idd=dlg_proc(0, DLG_CREATE)'
        srp    += l
        cids    = []
        for idC in range(app.dlg_proc(self.did, app.DLG_CTL_COUNT)):
            prC = _dlg_proc(self.did, app.DLG_CTL_PROP_GET, index=idC)
            cids+=[prC['name']]
            if ''==prC.get('hint', ''):                 prC.pop('hint', None)
            if ''==prC.get('tag', ''):                  prC.pop('tag', None)
            if ''==prC.get('cap', ''):                  prC.pop('cap', None)
            if ''==prC.get('items', None):              prC.pop('items')
            if prC.get('tab_stop', None):               prC.pop('tab_stop')
            if prC['type'] in ('label',):               prC.pop('tab_stop', None)
            if prC['type'] in ('bevel',):               (prC.pop('tab_stop', None)
                                                        ,prC.pop('tab_order', None))
            if prC['type'] not in ('listview'
                                  ,'checklistview'):    prC.pop('columns', None)
            if prC['type'] in ('label'
                              ,'bevel'
                              ,'button'):               prC.pop('val', None)
            if prC['type'] in ('button'):               prC.pop('act', None)
            if not prC.get('act', False):               prC.pop('act', None)
            if not prC.get('focused', False):           prC.pop('focused', None)
            if prC.get('vis', True):                    prC.pop('vis', None)
            if prC.get('en', True):                     prC.pop('en', None)
            name = prC['name']
            c_pr = self.ctrls[name].copy()
            c_pr = self._prepare_vl_it_cl(c_pr, c_pr, name)
            prC.update({k:v for k,v in c_pr.items() if k not in ('callback','on','menu')})
            srp+=l+f('idc=dlg_proc(idd, DLG_CTL_ADD,"{}");dlg_proc(idd, DLG_CTL_PROP_SET, index=idc, prop={})'
                    , prC.pop('type', None), out_attrs(prC, cattrs))
            srp+=l
        prD     = _dlg_proc(self.did, app.DLG_PROP_GET)
        prD.update(self.form)
#       srp    +=l
        fid     = prD.get('fid', prD['focused'])
        if fid not in cids:
            prD.pop('focused')
        srp    +=l+f('dlg_proc(idd, DLG_PROP_SET, prop={})', out_attrs(prD, fattrs))
        srp    +=l+(f('dlg_proc(idd, DLG_CTL_FOCUS, name="{}")', fid) if fid in cids else '')
        srp    +=l+  'dlg_proc(idd, DLG_SHOW_MODAL)'
        srp    +=l+  'dlg_proc(idd, DLG_FREE)'
        open(rerpo_fn, 'w', encoding='UTF-8').write(srp)
        
        return self
       #def gen_repro_code

    def __str__(self):
        return '<DlgAg id={}/{} cap="{}" #ctrls={} fid={} vals={}>'.format(
            self.did,   id(self),
            self.fattr('cap', ''),
            len(self.ctrls),
            self.focused(),
            self.vals(),
            )

    def __repr__(self):
        return self.__str__()
   #class DlgAg

def show_menu(mn_content, x, y, ag=None, cmd4all=None, repro_to_file=None, opts={}):
    """ mn_content      [{ cap:''
                         , tag:''
                         , en:T
                         , mark:''|'c'|'r'
                         , cmd:(lambda ag, tag:'')
                         , sub:[]
                         }
                        ]
        ag              DlgAg object
        x, y            Screen coords for menu top-left corner
        repro_to_file   File name (w/o path) to write reprocode with only menu_proc 
    """
    if cmd4all:
        set_all_for_tree(mn_content, 'sub', 'cmd', cmd4all)       # All nodes have same cmd

    c2m     = opts.get('c2m', False)
    
    rfn     = tempfile.gettempdir()+os.sep+repro_to_file            if repro_to_file else None
    print(f(r'exec(open(r"{}", encoding="UTF-8").read())', rfn))    if rfn else 0
    repro   = lambda line,*args,mod='a':(
                open(rfn, mod).write(line.format(*args)+'\n')       if rfn else 0)
    repro('import  cudatext as app', mod='w')                   # To sync conf- and repro-code
    
    def menu_callbk(it):
        u_callbk= it['cmd']
        upds    = u_callbk(ag, it.get('tag', ''))
        return ag.update(upds)  if ag else None                 # Allow to show menu w/a DlgAg
       #def menu_callbk
            
    def fill_mn(mid_prn, its):
        for it in its:
            if it['cap']=='-':
                app.menu_proc(  mid_prn, app.MENU_ADD, caption='-')
                repro("app.menu_proc(m{},app.MENU_ADD, caption='-')", mid_prn)
                continue#for it
            mid =(app.menu_proc(mid_prn, app.MENU_ADD, caption=it['cap'], command= lambda _it=it:menu_callbk(_it))     # _it=it solves lambda closure problem
                    if 'cmd' in it else 
                  app.menu_proc(mid_prn, app.MENU_ADD, caption=it['cap'])
                 )
            repro("m{}=app.menu_proc(m{},app.MENU_ADD, caption='{}')", mid, mid_prn, it['cap'])
            if it.get('key', ''):
                key = it['key']
                key = key.replace('Ctrl+', 'Meta+') if c2m else key
                app.menu_proc(      mid, app.MENU_SET_HOTKEY            , command=key)
                repro("app.menu_proc(m{},app.MENU_SET_HOTKEY            , command='{}')", mid, key)
                
            if it.get('mark', '')[:1]=='c' or it.get('mark', '')[:1]=='r' or it.get('ch', False) or it.get('rd', False):
                app.menu_proc(      mid, app.MENU_SET_CHECKED           , command=True)
                repro("app.menu_proc(m{},app.MENU_SET_CHECKED           , command=True)", mid)
            if it.get('mark', '')[:1]=='r' or it.get('rd', False):
                app.menu_proc(      mid, app.MENU_SET_RADIOITEM         , command=True)
                repro("app.menu_proc(m{},app.MENU_SET_RADIOITEM         , command=True)", mid)
                
            if not it.get('en', True):
                app.menu_proc(      mid, app.MENU_SET_ENABLED           , command=False)
                repro("app.menu_proc(m{},app.MENU_SET_ENABLED           , command=False)", mid)
            if 'sub' in it:
                fill_mn(mid, it['sub'])
       #def fill_mn
        
    mid_top = app.menu_proc(    0,       app.MENU_CREATE)
    repro("m{}=app.menu_proc(0,          app.MENU_CREATE)", mid_top)
    fill_mn(mid_top, mn_content)
    app.menu_proc(              mid_top, app.MENU_SHOW                  , command=f('{},{}', x, y))
    repro("app.menu_proc(       m{},     app.MENU_SHOW                  , command='{},{}')", mid_top, x, y)
    return []
   #def show_menu

OLD_PREFIX_FOR_USER_JSON = 'dlg_wrapper_fit_va_for_'
NEW_PREFIX_FOR_USER_JSON = 'dlg_ag_va_tunning_'
ENV2FITS= {
     'win':
        {'check'      :-2
        ,'radio'      :-2
        ,'edit'       :-3
        ,'button'     :-4
        ,'combo_ro'   :-4
        ,'combo'      :-3
        ,'checkbutton':-5
        ,'linklabel'  : 0
        ,'spinedit'   :-3
        }
    ,'unity':
        {'check'      :-3
        ,'radio'      :-3
        ,'edit'       :-5
        ,'button'     :-4
        ,'combo_ro'   :-5
        ,'combo'      :-6
        ,'checkbutton':-4
        ,'linklabel'  : 0
        ,'spinedit'   :-6
        }
    ,'mac':
        {'check'      :-1
        ,'radio'      :-1
        ,'edit'       :-3
        ,'button'     :-3
        ,'combo_ro'   :-2
        ,'combo'      :-3
        ,'checkbutton':-2
        ,'linklabel'  : 0
        ,'spinedit'   : 0   ##??
        }
    }

_FIT_REDUCTIONS  = {
     'linklabel': 'label'
    ,'edit_pwd' : 'edit'
    }
_fit_top_by_env__cache    = {}
def _fit_top_by_env__clear():
    global _fit_top_by_env__cache
    _fit_top_by_env__cache= {}
def _fit_top_by_env(what_tp, base_tp='label'):
    """ Get "fitting" to add to top of first control to vertical align inside text with text into second control.
        The fittings rely to platform: win, unix(kde,gnome,...), mac
    """
    what_tp = _FIT_REDUCTIONS.get(what_tp, what_tp)
    base_tp = _FIT_REDUCTIONS.get(base_tp, base_tp)
    if what_tp==base_tp:
        return 0
    if (what_tp, base_tp) in _fit_top_by_env__cache:            # Ready?
        pass;                  #log('cached what_tp, base_tp={}',(what_tp, base_tp))
        return _fit_top_by_env__cache[(what_tp, base_tp)]
    # Calc or restore, save in cache
    env     = get_desktop_environment()
    pass;                      #env = 'mac'
    fit4lb  = ENV2FITS.get(env, ENV2FITS.get('win'))
    fit     = 0
    if base_tp=='label':
        fit = apx.get_opt(NEW_PREFIX_FOR_USER_JSON+what_tp      # Query new setting
            , apx.get_opt(OLD_PREFIX_FOR_USER_JSON+what_tp      # Use old setting if no new one
                         ,fit4lb.get(what_tp, 0)))              # defaulf
        pass;                   fit_o=fit
        fit = _os_scale(app.DLG_PROP_GET, {'y':fit})['y']
        pass;                  #log('what_tp,fit_o,fit,h={}',(what_tp,fit_o,fit,_get_gui_height(what_tp)))
    else:
        fit = _fit_top_by_env(what_tp) - _fit_top_by_env(base_tp)
    pass;                      #log('what_tp, base_tp, fit={}',(what_tp, base_tp, fit))
    return _fit_top_by_env__cache.setdefault((what_tp, base_tp), fit)   # Save in cache
   #def _fit_top_by_env


DLG_CTL_ADD_SET = 26
_SCALED_KEYS = ('x', 'y', 'w', 'h'
            ,  'w_min', 'w_max', 'h_min', 'h_max'
            ,  'sp_l', 'sp_r', 'sp_t', 'sp_b', 'sp_a'
            )
def _os_scale(id_action, prop=None, index=-1, index2=-1, name=''):
    pass;                       log4fun=0                       # Order log in the function
    pass;                      #return prop
    pass;                      #log('prop={}',({k:prop[k] for k in prop if k in ('x','y')}))
    if not prop:
        return prop
    ppi     = app.app_proc(app.PROC_GET_SYSTEM_PPI, '')
    if ppi==96:
        return prop
    scale   = round(ppi/96, 4)
    pass;                       log('a={}({}),scale={},¬pr={}',id_action,get_const_name(id_action,'DLG_'),scale
                                    ,{k:prop[k] for k in prop if k in _SCALED_KEYS or k=='name'}) if iflog(log4fun,_log4mod) else 0
    if False:pass
    elif id_action in (app.DLG_PROP_SET     , app.DLG_PROP_GET
                      ,app.DLG_CTL_PROP_SET , app.DLG_CTL_PROP_GET
                      ,'scale', 'unscale'):
        
        def scale_up(prop_dct):
            for k in _SCALED_KEYS:
                if k in prop_dct and '_ready_'+k not in prop_dct:
                    prop_dct[k]   =             round(prop_dct[k] * scale)      # Scale!
        
        def scale_dn(prop_dct):
            for k in _SCALED_KEYS:
                if k in prop_dct and '_ready_'+k not in prop_dct:
                    prop_dct[k]   =             round(prop_dct[k] / scale)      # UnScale!
        
#       pass;                   print('a={}, ?? pr={}'.format(get_const_name(id_action,'DLG_'), {k:prop[k] for k in prop if k in _SCALED_KEYS or k=='name'}))
        if False:pass
        elif id_action==app.DLG_PROP_SET:                   scale_up(prop)
        elif id_action==app.DLG_CTL_PROP_SET and -1!=index: scale_up(prop)
        elif id_action==app.DLG_CTL_PROP_SET and ''!=name:  scale_up(prop)
        elif id_action==app.DLG_PROP_GET:                   scale_dn(prop)
        elif id_action==app.DLG_CTL_PROP_GET and -1!=index: scale_dn(prop)
        elif id_action==app.DLG_CTL_PROP_GET and ''!=name:  scale_dn(prop)

        elif id_action==  'scale':                          scale_up(prop)
        elif id_action=='unscale':                          scale_dn(prop)
        pass;                   log('a={}, ok ¬¬¬¬pr={}', get_const_name(id_action,'DLG_')
                                    , {k:prop[k] for k in prop if k in _SCALED_KEYS or k=='name'}) if iflog(log4fun,_log4mod) else 0
    return prop
   #def _os_scale

_gui_height_cache= { 
    'button'            :0
  , 'label'             :0
  , 'linklabel'         :0
  , 'combo'             :0
  , 'combo_ro'          :0
  , 'edit'              :0
  , 'spinedit'          :0
  , 'check'             :0
  , 'radio'             :0
  , 'checkbutton'       :0
  , 'filter_listbox'    :0
  , 'filter_listview'   :0
# , 'scrollbar'         :0
  }
def _get_gui_height(ctrl_type):
    """ Return real OS-specific height of some control
             'button'
             'label' 'linklabel'
             'combo' 'combo_ro'
             'edit' 'spinedit'
             'check' 'radio' 'checkbutton'
             'filter_listbox' 'filter_listview'
             'scrollbar'
    """
    pass;                       log4fun=0                       # Order log in the function
    global _gui_height_cache
    if 0 == _gui_height_cache['button']:
        for tpc in _gui_height_cache:
            _gui_height_cache[tpc]   = app.app_proc(app.PROC_GET_GUI_HEIGHT, tpc)
        pass;                  #log__('_gui_height_cache={}',(_gui_height_cache)      ,__=(log4fun,_log4mod))
        idd=app.dlg_proc(         0,    app.DLG_CREATE)
        for tpc in _gui_height_cache:
            idc=app.dlg_proc(   idd,    app.DLG_CTL_ADD, tpc)
            if idc is None: raise ValueError('Unknown type='+tpc)
            pass;              #log__('tpc,idc={}',(tpc,idc)      ,__=(log4fun,_log4mod))
            prc = {'name':tpc, 'x':0, 'y':0, 'w':1, 'cap':tpc
                , 'h':_gui_height_cache[tpc]}
            if tpc in ('combo' 'combo_ro'):
                prc['items']='item0'
            app.dlg_proc(       idd,    app.DLG_CTL_PROP_SET, index=idc, prop=prc)
        app.dlg_proc(           idd,    app.DLG_PROP_SET, prop={'x':-1000, 'y':-1000, 'w':100, 'h':100})
        app.dlg_proc(           idd,    app.DLG_SHOW_NONMODAL)

        ppi     = app.app_proc(app.PROC_GET_SYSTEM_PPI, '')
        if ppi!=96:
            # Try to scale height of controls
            scale   = ppi/96
            for tpc in _gui_height_cache:
                prc     = app.dlg_proc( idd,    app.DLG_CTL_PROP_GET, name=tpc)
                sc_h    = round(prc['h'] * scale)
                app.dlg_proc( idd,    app.DLG_CTL_PROP_SET, name=tpc, prop=dict(h=sc_h))

        for tpc in _gui_height_cache:
            prc = app.dlg_proc( idd,    app.DLG_CTL_PROP_GET, name=tpc)
            pass;              #log__('prc={}',(prc)      ,__=(log4fun,_log4mod))
            _gui_height_cache[tpc]   = prc['h']
        app.dlg_proc(           idd,    app.DLG_FREE)
        pass;                  #log__('_gui_height_cache={}',(_gui_height_cache)      ,__=(log4fun,_log4mod))
    
    return _gui_height_cache.get(ctrl_type, app.app_proc(app.PROC_GET_GUI_HEIGHT, ctrl_type))
   #def _get_gui_height

def _dlg_proc(id_dialog, id_action, prop='', index=-1, index2=-1, name=''):
    """ Wrapper on app.dlg_proc 
        1. To set/get dlg-props in scaled OS
        2. New command DLG_CTL_ADD_SET to set props of created ctrl
    """
    if id_action==app.DLG_SCALE:
        return
    pass;                       log4fun=0                       # Order log in the function
    pass;                       log__('id_a={}({}), ind,ind2,n={}, prop={}',id_action, get_const_name(id_action,'DLG_'), (index, index2, name), prop      ,__=(log4fun,_log4mod))
    if id_action==DLG_CTL_ADD_SET:  # Join ADD and SET for a control
        ctl_ind = app.dlg_proc( id_dialog, app.DLG_CTL_ADD, name, -1, -1, '')       # type in name
        if ctl_ind is None: raise ValueError('Unknown type='+name)
        return _dlg_proc(id_dialog, app.DLG_CTL_PROP_SET, prop, ctl_ind, -1, '')

    scale_on_set    = id_action in (app.DLG_PROP_SET, app.DLG_CTL_PROP_SET)
    scale_on_get    = id_action in (app.DLG_PROP_GET, app.DLG_CTL_PROP_GET)

    if scale_on_set:    _os_scale(id_action, prop, index, index2, name)
    res = app.dlg_proc(id_dialog, id_action, prop, index, index2, name)
    if scale_on_get:    _os_scale(id_action, res,  index, index2, name)
    return res
   #def _dlg_proc

def _gen_form_key(fprs):                                        # Gen key from form caption
    fm_cap  = fprs['cap']
    fm_cap  = fm_cap[:fm_cap.rindex(' (')]      if ' (' in fm_cap else fm_cap
    fm_cap  = fm_cap[:fm_cap.rindex(' [')]      if ' [' in fm_cap else fm_cap
    return fm_cap
   #def _gen_form_key
        
def _form_acts(act, fprs=None, did=None, key4store=None):
    """ Save/Restore pos of form """
    pass;                       log4fun=0                       # Order log in the function
    pass;                       log__('act, fprs, did={}',(act, fprs, did)      ,__=(log4fun,_log4mod))

    fprs    = _dlg_proc(did, app.DLG_PROP_GET)  if act=='save' and did else fprs
    fm_key  = key4store if key4store else _gen_form_key(fprs)
    pass;                       log__('fm_key, fprs={}',(fm_key, fprs)      ,__=(log4fun,_log4mod))
    if False:pass
    elif act=='move' and fprs:
        prev    = get_hist(fm_key)
        pass;                   log__('prev={}',(prev)      ,__=(log4fun,_log4mod))
        if not prev:    return fprs
#       if not fprs.get('resize', False):
        if 'resize' not in fprs.get('frame', ''):
            prev.pop('w', None)
            prev.pop('h', None)
        fprs.update(prev)
        pass;                   log__('!upd fprs={}',(fprs)      ,__=(log4fun,_log4mod))
        return fprs
    elif act=='save' and did:
        for (k,v) in {k:v for k,v in fprs.items() if k in ('x','y','w','h')}.items():
            set_hist([fm_key, k], v)
#       set_hist(fm_key, {k:v for k,v in fprs.items() if k in ('x','y','w','h')})
   #def _form_acts

######################################
#NOTE: tuning_valigns
######################################
class Command:
    def tuning_valigns(self):dlg_tuning_valigns()
   #class Command:
def dlg_tuning_valigns():
    pass;                      #log('ok')
    changed = False
    UP,DN   = '↑↑','↓↓'
    CTRLS   = ['check'
              ,'edit'
              ,'button'   
              ,'combo_ro' 
              ,'combo'    
              ,'checkbutton'
              ,'spinedit'
              ,'radio'
              ]
    CTRLS_SP= {'_sp'+str(1+ic):nc for ic, nc in enumerate(CTRLS)}

    FITS_OLD= {sp:_fit_top_by_env(nc) for sp, nc in CTRLS_SP.items()}
    fits    = {sp:_fit_top_by_env(nc) for sp, nc in CTRLS_SP.items()}           # See up_dn
    hints   = {sp:nc+': '+str(FITS_OLD[sp])+' (old), '+str(fits[sp])+' (new)' 
                for sp, nc in CTRLS_SP.items()}                                 # See up_dn

    def save():
        nonlocal changed
        for sp, nc in CTRLS_SP.items():
            fit = fits[sp]
            if fit==_fit_top_by_env(nc): continue#for
            apx.set_opt(NEW_PREFIX_FOR_USER_JSON+nc, fit)
            changed = True
           #for
        _fit_top_by_env__clear()    if changed else 0
        return None#hide
       #def save

    def up_dn(ag, cid, sht):
        pass;                  #log('cid,sht={}',(cid,sht))
        sp          = '_sp'+cid[-1]
        fits[sp]    = fits[sp] + sht
        hints[sp]   = CTRLS_SP[sp]+': '+str(FITS_OLD[sp])+' (old), '+str(fits[sp])+' (new)'
        return {'ctrls':[(cid ,dict(y=ag.cattr(cid, 'y')+sht ,hint=hints[sp] ))]}
       #def up_dn

    save_h  = _('Apply the tunings to controls of all dialogs.')
    sbleq   = ' ==============='
    seqeq   = '================='
    sbl44   = ' 4444444444444444'
    n4444   = 444444444
    sped_pr = f('0,{},1', n4444)
    cs      = CTRLS
    cnts    = [0
    ,('lb1' ,dict(tp='labl' ,y= 10              ,x=   5 ,w=110  ,cap=cs[0]+sbleq))
    ,('ch1' ,dict(tp='chck' ,y= 10+fits['_sp1'] ,x= 115 ,w=110  ,cap=seqeq      ,hint=hints['_sp1']             ))
    ,('up1' ,dict(tp='bttn' ,y= 10-3            ,x=-105 ,w= 50  ,cap=UP ,on=lambda ag,cid,d: up_dn(ag,'ch1',-1) ))
    ,('dn1' ,dict(tp='bttn' ,y= 10-3            ,x= -55 ,w= 50  ,cap=DN ,on=lambda ag,cid,d: up_dn(ag,'ch1', 1) ))
                
    ,('lb2' ,dict(tp='labl' ,y= 40              ,x=   5 ,w=110  ,cap=cs[1]+sbleq))
    ,('ed2' ,dict(tp='edit' ,y= 40+fits['_sp2'] ,x= 115 ,w=110                  ,hint=hints['_sp2']   ,val=seqeq))
    ,('up2' ,dict(tp='bttn' ,y= 40-3            ,x=-105 ,w= 50  ,cap=UP ,on=lambda ag,cid,d: up_dn(ag,'ed2',-1) ))
    ,('dn2' ,dict(tp='bttn' ,y= 40-3            ,x= -55 ,w= 50  ,cap=DN ,on=lambda ag,cid,d: up_dn(ag,'ed2', 1) ))
                
    ,('lb3' ,dict(tp='labl' ,y= 70              ,x=   5 ,w=110  ,cap=cs[2]+sbleq))
    ,('bt3' ,dict(tp='bttn' ,y= 70+fits['_sp3'] ,x= 115 ,w=110  ,cap=seqeq      ,hint=hints['_sp3']             ))
    ,('up3' ,dict(tp='bttn' ,y= 70-3            ,x=-105 ,w= 50  ,cap=UP ,on=lambda ag,cid,d: up_dn(ag,'bt3',-1) ))
    ,('dn3' ,dict(tp='bttn' ,y= 70-3            ,x= -55 ,w= 50  ,cap=DN ,on=lambda ag,cid,d: up_dn(ag,'bt3', 1) ))
                
    ,('lb4' ,dict(tp='labl' ,y=100              ,x=   5 ,w=110  ,cap=cs[3]+sbleq))
    ,('cbo4',dict(tp='cmbr' ,y=100+fits['_sp4'] ,x= 115 ,w=110  ,items=[seqeq]  ,hint=hints['_sp4']   ,val=0   ))
    ,('up4' ,dict(tp='bttn' ,y=100-3            ,x=-105 ,w= 50  ,cap=UP ,on=lambda ag,cid,d: up_dn(ag,'cbo4',-1)))
    ,('dn4' ,dict(tp='bttn' ,y=100-3            ,x= -55 ,w= 50  ,cap=DN ,on=lambda ag,cid,d: up_dn(ag,'cbo4', 1)))
                
    ,('lb5' ,dict(tp='labl' ,y=130              ,x=   5 ,w=110  ,cap=cs[4]+sbleq))
    ,('cb5' ,dict(tp='cmbx' ,y=130+fits['_sp5'] ,x= 115 ,w=110  ,items=[seqeq]  ,hint=hints['_sp5']   ,val=seqeq))
    ,('up5' ,dict(tp='bttn' ,y=130-3            ,x=-105 ,w= 50  ,cap=UP ,on=lambda ag,cid,d: up_dn(ag,'cb5',-1) ))
    ,('dn5' ,dict(tp='bttn' ,y=130-3            ,x= -55 ,w= 50  ,cap=DN ,on=lambda ag,cid,d: up_dn(ag,'cb5', 1) ))
                
    ,('lb6' ,dict(tp='labl' ,y=160              ,x=   5 ,w=110  ,cap=cs[5]+sbleq))
    ,('chb6',dict(tp='chbt' ,y=160+fits['_sp6'] ,x= 115 ,w=110  ,cap=seqeq[:10] ,hint=hints['_sp6']             ))
    ,('up6' ,dict(tp='bttn' ,y=160-3            ,x=-105 ,w= 50  ,cap=UP ,on=lambda ag,cid,d: up_dn(ag,'chb6',-1)))
    ,('dn6' ,dict(tp='bttn' ,y=160-3            ,x= -55 ,w= 50  ,cap=DN ,on=lambda ag,cid,d: up_dn(ag,'chb6', 1)))
                
    ,('lb7' ,dict(tp='labl' ,y=190              ,x=   5 ,w=110  ,cap=cs[6]+sbl44))
    ,('sp7' ,dict(tp='sped' ,y=190+fits['_sp7'] ,x= 115 ,w=110  ,props=sped_pr  ,hint=hints['_sp7']   ,val=n4444))
    ,('up7' ,dict(tp='bttn' ,y=190-3            ,x=-105 ,w= 50  ,cap=UP ,on=lambda ag,cid,d: up_dn(ag,'sp7',-1) ))
    ,('dn7' ,dict(tp='bttn' ,y=190-3            ,x= -55 ,w= 50  ,cap=DN ,on=lambda ag,cid,d: up_dn(ag,'sp7', 1) ))
                
    ,('lb8' ,dict(tp='labl' ,y=220              ,x=   5 ,w=110  ,cap=cs[7]+sbleq))
    ,('rd8' ,dict(tp='rdio' ,y=220+fits['_sp8'] ,x= 115 ,w=110  ,cap=seqeq      ,hint=hints['_sp8']             ))
    ,('up8' ,dict(tp='bttn' ,y=220-3            ,x=-105 ,w= 50  ,cap=UP ,on=lambda ag,cid,d: up_dn(ag,'rd8',-1) ))
    ,('dn8' ,dict(tp='bttn' ,y=220-3            ,x= -55 ,w= 50  ,cap=DN ,on=lambda ag,cid,d: up_dn(ag,'rd8', 1) ))
                
    ,('save',dict(tp='bttn' ,y=-30              ,x=-220 ,w=110  ,cap=_('&Save') ,on=lambda ag,cid,d:save() ,hint=save_h))
    ,('-'   ,dict(tp='bttn' ,y=-30              ,x=-105 ,w=100  ,cap=_('Cancel'),on=CB_HIDE ))
    ][1:]
    ag  = DlgAg(form=dict(
                cap=_('Tuning text vertical alignment for control pairs')
            ,   w=335, h=310-30)
        ,   ctrls=cnts 
        ,   fid = '-'
        ,   opts={'negative_coords_reflect':True}
        )
#   ag.gen_repro_code('repro_tuning_valigns.py')
    ag.show()    #NOTE: dlg_valign
    return changed
   #def tuning_valigns

if __name__ == '__main__' :
    # To start the tests run in Console
    #   exec(open(path_to_the_file, encoding="UTF-8").read())

    app.app_log(app.LOG_CONSOLE_CLEAR, 'm')
#   print('Start all tests')
    if -2==-2:
        for smk in [smk for smk 
            in  sys.modules                             if 'cuda_kv_dlg.tests.test_dlg_ag' in smk]:
            del sys.modules[smk]        # Avoid old module 
        import                                              cuda_kv_dlg.tests.test_dlg_ag
        import unittest
        suite = unittest.TestLoader().loadTestsFromModule(  cuda_kv_dlg.tests.test_dlg_ag)
        unittest.TextTestRunner(verbosity=0).run(suite)
        
#   if -1== 1:
#       print('Start test1: dlg: (label, edit, button), (tid, call, update, hide, on_exit)')
#       print('Stop test1')
#   print('Stop all tests')
'''
ToDo
[+][kv-kv][13feb19] Extract from cd_plug_lib.py
[+][kv-kv][13feb19] Set tests
[+][kv-kv][15feb19] Add proxy for all form events
[+][kv-kv][15feb19] Add more calc for ctrl position
[+][kv-kv][15feb19] ? Reorder params in fattrs ?
[ ][kv-kv][15feb19] ? Cancel form moving by opt ?
[+][kv-kv][15feb19] Allow r=-10 as <gap to right border> by opt
[ ][kv-kv][15feb19] Allow repro from any state
[+][kv-kv][18feb19] Anchors
[+][kv-kv][18feb19] Menu
[+][kv-kv][18feb19] dlg_valigns
[ ][kv-kv][24feb19] Test for live attr on_exit
[+][kv-kv][25feb19] Allow dict for ctrls values
[ ][kv-kv][25feb19] Test focused in fattr
[+][at-kv][06mar19] ag set first in all cb
[-][at-kv][06mar19] Use "return False" as "return None" in cb
[ ][at-kv][06mar19] Test for panel in panel
[+][at-kv][06mar19] def handle for control/form
[+][at-kv][06mar19] negative_xy_as_reflect -> negative_coords_reflect
[+][at-kv][06mar19] nonmodal
[+][at-kv][06mar19] reset
[ ][kv-kv][11mar19] ! border, on update
[+][kv-kv][11mar19] ? copy live vals to mem 'val' after hide ?
[ ][kv-kv][14mar19] ? tracer via opts
[+][kv-kv][14mar19] VERSION
[ ][kv-kv][20mar19] i18n
[+][kv-kv][22mar19] Attr synonims: au/autosize, cols/columns, ...
[+][kv-kv][24mar19] ? Auto-restore col-widths for listview and same
[+][kv-kv][24mar19] ? Add * as col-width value for listview and same
[ ][kv-kv][26mar19] ? Chain for more than one event-callbacks
[ ][kv-kv][29mar19] ! form handlers in update()
[+][at-kv][01apr19] Ctrl <-> Meta for MacOS
'''
