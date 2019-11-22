''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '1.7.11 2019-09-09'
ToDo: (see end of file)
'''

import  re, os

import          cudatext            as app
from            cudatext        import ed
from            cudatext_keys   import *
import          cudatext_cmd        as cmds
import          cudax_lib           as apx
try:    from    cuda_kv_base    import *    # as separated plugin
except: from     .cd_kv_base    import *    # as part of this plugin
try:    from    cuda_kv_dlg     import *    # as separated plugin
except: from     .cd_kv_dlg     import *    # as part of this plugin

try:# I18N
    _   = get_translation(__file__)
except:
    _   = lambda p:p

pass;                           LOG = (-2== 2)                  # Do or dont logging.
pass;                           _log4mod = LOG_FREE             # Order log in the module

def go_back_tab():
    if app.app_api_version()<'1.0.253':
        return app.msg_status(NEED_UPDATE)
    pass;                      #log("###",( ))
    eds         = [app.Editor(h) for h in app.ed_handles()]     # Native order
    ed_tats     = [(ed_, ed_.get_prop(app.PROP_ACTIVATION_TIME, '')) for ed_ in eds]
    ed_tats     = [(at, ed_) for (ed_, at) in ed_tats if at]    # Only activated
    if len(ed_tats)<2:
        return app.msg_status(_('No yet other activated tab'))
    ed_tats.sort(reverse=True, key=lambda ae:ae[0])
    ed_back     = ed_tats[1][1]
    ed_back.focus()
   #def go_back_tab


def go_back_dlg():
    pass;                       log4fun=0                       # Order log in the function
    if app.app_api_version()<'1.0.253':
        return app.msg_status(NEED_UPDATE)
    pass;                       log__("",( )      ,__=(log4fun,_log4mod))
#   scam    = app.app_proc(app.PROC_GET_KEYSTATE, '')
    if 'c' not in app.app_proc(app.PROC_GET_KEYSTATE, ''):      # User already is released Ctrl
        return go_back_tab()
    cfg_keys= get_plugcmd_hotkeys('go_back_dlg')
    pass;                      #log('ok scam,cfg_keys={}',(scam,cfg_keys))
    act_clr     = rgb_to_int(232,232,232)
    pss_clr     = rgb_to_int(216,216,216)
        
    side_pns    = app.app_proc(app.PROC_SIDEPANEL_ENUM,   '').split('\n')
    botm_pns    = app.app_proc(app.PROC_BOTTOMPANEL_ENUM, '').split('\n')
    panels      = [((app.PROC_SIDEPANEL_ACTIVATE,  (pn,True)), pn)  for pn in side_pns] \
                + [( None                                    , '')                    ] \
                + [((app.PROC_BOTTOMPANEL_ACTIVATE,(pn,True)), pn)  for pn in botm_pns]
    panels      = [(act, pn)     for (act, pn) in panels if pn!='Menu']
    eds         = [app.Editor(h) for h in app.ed_handles()]     # Native order
    ed_tats     = [(ed_, ed_.get_prop(app.PROP_ACTIVATION_TIME, '')) for ed_ in eds]
    ed_tats     = [(at, ed_) for (ed_, at) in ed_tats if at]    # Only activated
    ed_tats.sort(reverse=True, key=lambda ae:ae[0])
    eds         = [ed_       for (at, ed_) in ed_tats]          # Sorted by activation time
    eds         = eds[:apx.get_opt('ui_max_history_edits', 20)] # Cut olds
    eds         = eds if eds else [ed]
    eds_hist    = [(ed_, ed_.get_prop(app.PROP_TAB_ID, '')
                       , ed_.get_prop(app.PROP_TAB_TITLE) 
                       , ed_.get_filename()
                   ) for ed_ in eds]
    pass;                      #log('eds_hist={}',(eds_hist))
    start_sel   = min(1, len(eds_hist)-1)
    pass;                      #log('start_sel,len(eds_hist)={}',(start_sel,len(eds_hist)))
    ed_back     = eds_hist[start_sel][0]
    panel_to    = None
    start_pnls  = get_hist('switcher.start_panel', 'Code tree')

    def do_show(ag, key, data=None):
        pass;                   log__("",( )      ,__=(log4fun,_log4mod))
        
        if 'c' not in app.app_proc(app.PROC_GET_KEYSTATE, ''):  ag.hide()
        app.timer_proc(app.TIMER_START_ONE, lambda tag:         ag.hide() 
                                        if 'c' not in app.app_proc(app.PROC_GET_KEYSTATE, '') else 0
                      ,200)
        return []
       #def do_show
        
    def do_key_up(ag, key, data=None):
        scam    = data if data is not None else app.app_proc(app.PROC_GET_KEYSTATE, '')
        return None if 'c' not in scam else []
       #def do_key_up
        
    def do_key_down(ag, key, data=None):
        nonlocal ed_back, panel_to
        scam    = data if data is not None else app.app_proc(app.PROC_GET_KEYSTATE, '')
        pass;                  #log('scam={}',(scam))
        k2K     = dict(s='Shift+', c='Ctrl+', a='Alt+')
        hotkey  = ''.join(k2K[k] for k in scam) + chr(key)
        pass;                  #log('key,hotkey,cfg_keys={}',(key,hotkey,cfg_keys))
        to_othr = False
        sel_to  = ''
        if 0:pass
        elif key==VK_ENTER:                             ag.hide()
        elif key==VK_ESCAPE:    panel_to=ed_back=None;  ag.hide()
            
        elif key in (VK_LEFT, VK_RIGHT):to_othr = True
            
        elif key==VK_DOWN:              sel_to  = 'next'
        elif key==VK_UP:                sel_to  = 'prev'
        elif key==VK_TAB and scam== 'c':sel_to  = 'next'
        elif key==VK_TAB and scam=='sc':sel_to  = 'prev'
        elif hotkey in cfg_keys:        sel_to  = 'next'
        else:   return []
        pass;                  #log('sel_to,to_othr={}',(sel_to,to_othr))
            
        fid = ag.focused()
        if to_othr:
            fid = 'pnls' if fid=='tabs' else 'tabs'
            ag.update(dict(
                fid     =fid
            ,   ctrls   =[('tabs',dict(color=act_clr if fid=='tabs' else pss_clr))
                         ,('pnls',dict(color=act_clr if fid=='pnls' else pss_clr ))
                         ]
            ))
            ed_back     = None if fid=='pnls' else eds_hist[ag.val('tabs')][0]
            panel_to    = None if fid=='tabs' else panels[  ag.val('pnls')]
            
        pass;                  #log('sel_to={}',(sel_to))
        if sel_to:
            ed_back     = None
            panel_to    = None
            shft        = 1 if sel_to=='next' else -1
            if fid=='tabs':
                sel = (ag.val('tabs') + shft) % len(eds_hist)
                pass;          #log("shft,tabs.val,sel={}",(shft,ag.val('tabs'),sel))
                ed_back     = eds_hist[sel][0]
                pass;          #log('sel={}',(ag.val('tabs'), sel))
                ag.update({'vals':{'tabs':sel}})
            if fid=='pnls':
                sel = (ag.val('pnls') + shft) % len(panels)
                panel_to    = panels[sel]
                if not panel_to[0]:
                    sel = (sel              + shft) % len(panels)
                    panel_to= panels[sel]
                pass;          #log('sel={}',(ag.val('pnls'), sel))
                ag.update({'vals':{'pnls':sel}})
            
        return False                                            # Stop event
       #def do_key_down
        
    def do_select(ag, aid, data=''):
        nonlocal ed_back, panel_to
        sel     = ag.val(aid)
        pass;                  #log('sel={}',(sel))
        if aid=='tabs':
            ed_back = eds_hist[sel][0]
            panel_to= None
        if aid=='pnls':
            ed_back = None
            panel_to= panels[sel]
        return []
        
    def do_dclk(ag, aid, data=''):
        do_select(ag, aid)
        if aid=='pnls' and not panel_to[0]:
            return []                                           # Ignore
        return None                                             # Close dlg
       #def do_dclk
        
    panls       = [(pn if pn else '—'*100) for act,pn in panels]
    items       = [ed_tit for (ed_, ed_tid, ed_tit, ed_fn) in eds_hist]
    if 'c' not in app.app_proc(app.PROC_GET_KEYSTATE, ''):      # User already is released Ctrl
        return go_back_tab()
    ag_swch     = DlgAg(
        form    = dict(cap=_('Switcher'), w=350, h=300, frame='resize'
                     ,on_show       =do_show
                     ,on_key_down   =do_key_down
                     ,on_key_up     =do_key_up
                     )
    ,   ctrls   = [0
         ,('tabs',dict(tp='libx',items=items,ali=ALI_CL         ,color=act_clr  ,on=do_select   ,on_click_dbl=do_dclk ,on_click=do_dclk   ))
         ,('pnls',dict(tp='libx',items=panls,ali=ALI_RT ,w=110  ,color=pss_clr  ,on=do_select   ,on_click_dbl=do_dclk ,on_click=do_dclk   ))
                ][1:]
    ,   fid     = 'tabs'
    ,   vals    = dict( tabs=start_sel
                       ,pnls=panls.index(start_pnls) if start_pnls in panls else 0
                      )
    )
#   ag_swch.gen_repro_code('repro_dlg_switcher.py')
    pass;                      #log("app.app_proc(app.PROC_GET_KEYSTATE, '')={}",(app.app_proc(app.PROC_GET_KEYSTATE, '')))
    if 'c' not in app.app_proc(app.PROC_GET_KEYSTATE, ''):      # User already is released Ctrl
        return go_back_tab()
    ag_swch.show()
    pass;                      #log("",())
    if ed_back:
        ed_back.focus()
    elif panel_to and panel_to[0]:
        set_hist('switcher.start_panel', panel_to[1])
        app.app_proc(*(panel_to[0]))
   #def go_back_dlg


def _activate_tab(group, tab_ind):
    pass;                       LOG and log('group, tab_ind={}',(group, tab_ind))
    for h in app.ed_handles():
        edH = app.Editor(h)
        pass;                   LOG and log('h.g h.t={}',(edH.get_prop(app.PROP_INDEX_GROUP),edH.get_prop(app.PROP_INDEX_TAB)))
        if ( group  ==edH.get_prop(app.PROP_INDEX_GROUP)
        and  tab_ind==edH.get_prop(app.PROP_INDEX_TAB)):
            pass;               LOG and log('found',())
            edH.focus()
            return True
    return False
   #def _activate_tab


def _activate_last_tab(group):
    pass;                      #LOG and log('')
    max_ind = -1
    last_ed = None
    for h in app.ed_handles():
        edH = app.Editor(h)
        if (group  == edH.get_prop(app.PROP_INDEX_GROUP)
        and max_ind < edH.get_prop(app.PROP_INDEX_TAB)):
            max_ind = edH.get_prop(app.PROP_INDEX_TAB)
            last_ed = edH
    if last_ed is not None:
        last_ed.focus()
   #def _activate_last_tab


def _activate_near_tab(gap):
    pass;                      #LOG and log('gap={}',gap)
    eds     = [app.Editor(h) for h in app.ed_handles()]
    if 1==len(eds):    return
    gtes    = [(e.get_prop(app.PROP_INDEX_GROUP), e.get_prop(app.PROP_INDEX_TAB), e) for e in eds]
    gtes    = list(enumerate(sorted(gtes)))
    group   = ed.get_prop(app.PROP_INDEX_GROUP)
    t_ind   = ed.get_prop(app.PROP_INDEX_TAB)
    for g_ind, (g, t, e) in gtes:
        if g==group and t==t_ind:
            g_ind   = (g_ind+gap) % len(gtes)
            gtes[g_ind][1][2].focus()
   #def _activate_near_tab


def move_tab():
    old_pos = ed.get_prop(app.PROP_INDEX_TAB)
    new_pos = app.dlg_input('New position', str(old_pos+1))
    if new_pos is None: return
    new_pos = max(1, int(new_pos))
    ed.set_prop(app.PROP_INDEX_TAB, str(new_pos-1))
   #def move_tab


def find_tab():
    pttn = app.dlg_input('What to find in tab title', '')
    if pttn is None: return
    for h in app.ed_handles():
        ed_ = app.Editor(h)
        if pttn in ed_.get_prop(app.PROP_TAB_TITLE):
            ed_.focus()
            return 
    app.msg_status(f(_('No tab with "{}" in title'), pttn))
   #def find_tab


def to_tab_ask_num():
    while True:
        grp_num = app.dlg_input('What tab number to activate? Input: [group:]number', '')
        if grp_num is None: return
        if re.match(r'(\d:)?\d+', grp_num):
            break
    me_grp  = ed.get_prop(app.PROP_INDEX_GROUP)
    grp     = int(grp_num.split(':')[0])-1 if ':' in grp_num else me_grp
    num     = int(grp_num.split(':')[1])-1 if ':' in grp_num else int(grp_num)-1
    for h in app.ed_handles():
        ed_ = app.Editor(h)
        if grp == ed_.get_prop(app.PROP_INDEX_GROUP) and \
           num == ed_.get_prop(app.PROP_INDEX_TAB):
            ed_.focus()
    app.msg_status(f(_('No tab "{}"'), grp_num))
   #def to_tab_ask_num


def _activate_tab_other_group(what_tab='next', what_grp='next'):
    grps    = apx.get_groups_count()
    if 1==grps:  return
    me_grp  = ed.get_prop(app.PROP_INDEX_GROUP)
    op_grp  = (me_grp+1)%grps \
                if what_grp=='next' else \
              (me_grp-1)%grps
    op_hs   = [h for h in app.ed_handles()
                if app.Editor(h).get_prop(app.PROP_INDEX_GROUP)==op_grp]
    if len(op_hs)<2:  return
    op_ed   = app.ed_group(op_grp)
    op_ind  = op_ed.get_prop(app.PROP_INDEX_TAB)
    op_ind  = (op_ind+1)%len(op_hs)     if what_tab=='next' else \
              (op_ind-1)%len(op_hs)     if what_tab=='prev' else \
              0                         if what_tab=='frst' else \
              len(op_hs)-1              if what_tab=='last' else \
              op_ind
    app.Editor(op_hs[op_ind]).focus()
    me_ed   = app.ed_group(me_grp)
    me_ed.focus()
   #def _activate_tab_other_group


def close_tab_from_other_group(what_grp='next'):
    if app.app_api_version()<'1.0.139': return app.msg_status(NEED_UPDATE)
    grps    = apx.get_groups_count()
    if 1==grps: return
    me_grp  = ed.get_prop(app.PROP_INDEX_GROUP)
    cl_grp  = (me_grp+1)%grps \
                if what_grp=='next' else \
              (me_grp-1)%grps
    if not [h for h in app.ed_handles() if app.Editor(h).get_prop(app.PROP_INDEX_GROUP)==cl_grp]:
        return app.msg_status(_('No files in group'))
    cl_ed   = app.ed_group(cl_grp)
    cl_ed.focus()
    cl_ed.cmd(cmds.cmd_FileClose)
    me_ed   = app.ed_group(me_grp)
    me_ed.focus()
   #def close_tab_from_other_group

