''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
    Alexey Torgashin (CudaText)
Version:
    '1.7.35 2021-09-17'
ToDo: (see end of file)
'''

import  re, os, sys, webbrowser
from            operator        import itemgetter

import          cudatext            as app
from            cudatext        import ed
from            cudatext_keys   import *
import          cudatext_cmd        as cmds
import          cudax_lib           as apx

from            .cd_kv_base     import *        # as part of this plugin
from            .cd_kv_dlg      import *        # as part of this plugin

try:# I18N
    _   = get_translation(__file__)
except:
    _   = lambda p:p

pass;                           import cudatext_keys
pass;                           _log4mod = LOG_FREE  # Order log in the module

#d       = dict
d       = dcta      # To use keys as attrs: o=dcta(a=b); x=o.a; o.a=x
C1      = chr(1)
def flatten(xs):
    for x in xs:
        if isinstance(x, (tuple, list)):
            for xx in flatten(x):   yield xx
        else:                       yield x
msg_box     = lambda     tx, bts_ico=app.MB_OK: app.msg_box(       tx, bts_ico)
msg_box_ex  = lambda cp, tx, bts=['OK'] :       app.msg_box_ex(cp, tx, bts, app.MB_ICONINFO)


class RiL:
    HIST_KEY= 'find.replace_in_lines'

    FORM_CB = _('Replace all in Lines')                         # RaiL
    FORM_C  = FORM_CB+' '+_('(Enter in first field to find)')   # RaiL
    HELP_TX = _('''
• [Shift+]Enter in "Find" field to search [previous] next fragment.
• Ctlr+Down/Up to copy pattern lower/upper.
• Command "Restore initial selection" (Shift+Esc) tries to restore only first of initial carets.
• RegExp engine from CudaText is used. Names of RegEx sub-groups are $1, $2...
    ''').strip()
    REEX_H  = _('Regular expression'
                '\rRegEx engine from CudaText is used')
    CASE_H  = _('Case sensitive')
    WORD_H  = _('Whole words')
    SETS_H  = _('Kit of pairs to replace'
                '\rAlt+Left/Right - load previous/next pair'
                '\rAlt+Shift+Left/Right - activate previous/next kit')
    WHAT_H  = _('Pattern to search'
                '\rEnter - to find next'
                '\rShift+Enter - to find previous')
    REPL_H  = _('Pattern to replace'
                '\rRegExp sub-groups are $1, $2, ...')
#   REPL_H  = _('Pattern to replace\rEnter - to replace next')
    RPLA_H  = _('Replace all')
    RPLS_H  = _('Replace all for all pairs from the kit')
    DEF_SET = _('<def>')

    CL_WARN = apx.html_color_to_int('#A00000')
    CL_INFO = apx.html_color_to_int('#808080')
    _stus   = ''
    @staticmethod
    def msg_d(s,t='i',a=0):
        RiL._stus = RiL._stus+s if a else s
        return                                     d(cap=RiL._stus, font_color=RiL.CL_INFO if t=='i' else RiL.CL_WARN)
#   msg_d   = lambda   s,t='i',a=0:                d(cap=s, font_color=RiL.CL_INFO if t=='i' else RiL.CL_WARN)
    msg_s   = lambda   s,t='i',a=0:         d(stus=RiL.msg_d(s,t,a))
    msg     = lambda   s,t='i',a=0: d(ctrls=RiL.msg_s(s,t,a)       )
    msg_f   = lambda f,s,t='i',a=0: d(ctrls=RiL.msg_s(s,t,a), fid=f)

    st2item = lambda n, st: f('&{}: {} (#{})', n+1, st.nm, len(st.ps))
    st_pr_rc= lambda    pr: ( ('r' if pr.re else '')
                            + ('c' if pr.cs else '')
                            + ('w' if pr.wd else '') )
    st_pr_cw= lambda    pr: ( ('[' if pr.re or pr.cs or pr.wd else '')
                            + ('.' if pr.re else '')
                            + ('c' if pr.cs else '')
                            + ('w' if pr.wd else '')
                            + ('] '  if pr.re or pr.cs or pr.wd else '') )
    st_pr   = lambda    pr: f('{}"{}" -> "{}"'
                            , RiL.st_pr_cw(pr)
                            , pr.f, pr.r)
    st_pr_n = lambda n, pr: f('{}: {}', n+1, RiL.st_pr(pr))
    st_pr_mn= lambda n, pr: re.sub(r'^(\d*)(\d: )', r'\1&\2', RiL.st_pr_n(n, pr))
    sets_items  = lambda sts: [RiL.st2item(n,st).replace('&', '') for n,st in enumerate(sts)]


    def __init__(self):
        M,m         = type(self),self
        pass;                   log4fun=2                       # Order log in the function

        m.ed_crts   = ed.get_carets()                           # Carets at start/activate
        m.opts      = d(reex=False,case=False,word=False
                    ,   what=''                                 # Last value  in "what"
                    ,   whtl=[]                                 # List values in "what"
                    ,   repl=''                                 # Last value  in "repl" 
                    ,   rpll=[]                                 # List values in "repl"
                    ,   sets=[d(nm=M.DEF_SET,ps=[])]            # ps=[d(f='a', r='b', re=False, cs=False, wd=False)]
                    ,   aset=0                                  # Last active in "sets"
                    ,   usel=False                              # Use ed sel
                    ,   fitn=False                              # Autofit Replace pattern
                    ,   anxt=False                              # Autoload next pair atfer ReplAll
                    ,   pfid='what')                            # Last fid
        m.opts.update(get_hist(M.HIST_KEY, m.opts, object_pairs_hook=dcta))
        pass;                  #log("m.opts={}",(m.opts)) if log4fun else 0
        pass;                  #log("m.opts.sets={}",len(m.opts.sets)) if log4fun else 0
       #def __init__
    
    
    def on_exit(self, ag):
        M,m         = type(self),self
        m.opts.pfid = ag.focused()
        pass;                  #log("m.opts={}",(m.opts))
        set_hist(M.HIST_KEY, deep_upd((m.opts, ag.vals(['reex','case','word','what','repl']), {'aset':ag.val('sets')})))
       #def on_exit


    def show(self):
        M,m         = type(self),self
        pass;                   log4fun=0                       # Order log in the function

#       m.ed_crts   = ed.get_carets()                           # Carets at start/activate
#       m.opts      = d(reex=False,case=False,word=False
#                   ,   what=''                                 # Last value  in "what"
#                   ,   whtl=[]                                 # List values in "what"
#                   ,   repl=''                                 # Last value  in "repl" 
#                   ,   rpll=[]                                 # List values in "repl"
#                   ,   sets=[d(nm=M.DEF_SET,ps=[])]            # ps=[d(f='a', r='b', re=False, cs=False, wd=False)]
#                   ,   aset=0                                  # Last active in "sets"
#                   ,   usel=False                              # Use ed sel
#                   ,   fitn=False                              # Autofit Replace pattern
#                   ,   anxt=False                              # Autoload next pair atfer ReplAll
#                   ,   pfid='what')                            # Last fid
#       m.opts.update(get_hist(M.HIST_KEY, m.opts, object_pairs_hook=dcta))
#       pass;                   log("m.opts={}",(m.opts)) if log4fun else 0

        edsel       = ed.get_text_sel()
        if m.opts.usel and edsel:
            m.opts.what = edsel
            if '\r' in m.opts.what or '\n' in m.opts.what:
                m.opts.what = ''
            elif m.opts.fitn:
                repl    = m.work('offer_repl', m.opts.what)
                pass;          #log("repl={}",(repl))
                if repl:
                    m.opts.repl = repl
        
        bttn_h  = get_gui_height('bttn')
        
        sits    = M.sets_items(m.opts.sets)
        WIN_MAC = (get_desktop_environment() in ('win', 'mac'))
        YG      = 0 if WIN_MAC else 3
        ctrls   = d(
            reex=d(tp='chbt',tid='menu' ,x=80+38*0  ,w=38   ,cap='&.*'          ,hint=M.REEX_H          # Alt+.
          ),case=d(tp='chbt',tid='menu' ,x=80+38*1  ,w=38   ,cap='&cC'          ,hint=M.CASE_H          # Alt+C
          ),word=d(tp='chbt',tid='menu' ,x=80+38*2  ,w=38   ,cap='"&w"'         ,hint=M.WORD_H          # Alt+W
          ),stu_=d(tp='bvel',y  = 5     ,x=80+38*3+5,r=-52+4,h=bttn_h           ,ex0='1'      ,a='r>'
          ),stus=d(tp='labl',tid='menu' ,x=80+38*3+9,r=-52  ,cap=''                             ,a='r>'     
          ),menu=d(tp='bttn',y  = 5     ,x=-5-38    ,w=38   ,cap='&='                           ,a='>>' # Alt+=
          ),wha_=d(tp='labl',tid='what' ,x= 5       ,w=80-10,cap='>*'+_('&Find'),hint=M.WHAT_H          # Alt+F
          ),what=d(tp='cmbx',y  =35+YG*1,x=80       ,r=-48  ,items=m.opts.whtl                  ,a='r>' # 
          ),rep_=d(tp='labl',tid='repl' ,x= 5       ,w=80-10,cap='>'+_('&Replace'),hint=M.REPL_H        # Alt+R
          ),repl=d(tp='cmbx',y  =65+YG*2,x=80       ,r=-48  ,items=m.opts.rpll                  ,a='r>' # 
          ),rpla=d(tp='bttn',tid='repl' ,x=-5-38    ,w=38   ,cap=_('&All')      ,hint=M.RPLA_H  ,a='>>' # Alt+A
          ),set_=d(tp='labl',tid='sets' ,x= 5       ,w=80-10,cap='>'+_('&Kits') ,hint=M.SETS_H          # Alt+K
          ),sets=d(tp='cmbr',y  =95+YG*3,x=80       ,r=-48  ,items=sits                         ,a='r>' # 
          ),rpls=d(tp='bttn',tid='sets' ,x=-5-38    ,w=38   ,cap=_('A&LL')      ,hint=M.RPLS_H  ,a='>>' # Alt+L
                    ))
        ctrls.menu.on_menu  = m.do_menu
        ctrls.menu.on       = m.do_menu
        for ctrl in ctrls.values():
            if  ctrl.tp not in ('cmbx', 'cmbr'):             # Tab stops only in these
                ctrl.sto    = False
            if  ctrl.tp in ('chbt', 'bttn', 'cmbr') and 'on' not in ctrl:
                ctrl.on     = m.do_acts

        ag      = DlgAg(
            form    =d(cap=M.FORM_C, w=500, h=125+YG*3, h_max=125+YG*3      # Only horz resize
                      ,on_key_down=m.do_keys
                      ,frame='resize')
        ,   ctrls   =ctrls
        ,   fid     =m.opts.pfid
        ,   vals    =d(**{k:m.opts[k] for k in ('reex','case','word')}
                        , what=m.opts.what
                        , repl=m.opts.repl
                        , sets=m.opts.aset)
        ,   opts    =d(negative_coords_reflect=True)
        )
        pass;                  #ag.gen_repro_code('repro_dlg_ril.py')

        ag.show(on_exit=self.on_exit)
       #def show


    def do_menu(self, ag, aid, data=''):
        M,m         = type(self),self
        pass;                  #return []
        sets    = m.opts.sets
        cset    = sets[m.opts.aset]

        nm_sets=[
      d(                 cap=M.st2item(n, st)                   ,key=(f'Ctrl+{n+1}'       if n<9 else '')   ,sub=[(
    ),d(tag=f'stAC{n}'  ,cap=f(_('Activate kit "{}"'),st.nm)    ,key=(f'Ctrl+{n+1}'       if n<9 else '')
    ),d(tag=f'stRA{n}'  ,cap=M.RPLS_H+'...'                     ,key=(f'Ctrl+Shift+{n+1}' if n<9 else '')
    ),d(             cap='-'
    )][1:]+[
      d(tag=f'stLP{n}_{np}'
                        ,cap=M.st_pr_mn(np, pr))                                for np,pr in enumerate(st.ps)]
      ) for n,st in enumerate(sets)
                ]+[(
    ),d(                 cap='-'
    ),d(tag='stse'      ,cap=_('Edit kits...')                      ,keys='Ctrl+K'
    ),d(tag='impt'      ,cap=_('&Import from Replace history...') ,en=app.app_api_version()>='1.0.347'
    ),d(                 cap=_('Rem&ove kit')           ,en=bool(sets)  ,sub=[
      d(tag=f'stRM{n}',cap=M.st2item(n, st))                                    for n,st in enumerate(sets)]
    ),d(tag='stsw'      ,cap=_('&Change kits order...') ,en=len(sets)>1
    )][1:]
        rpls_c      = f(_('Replace A&LL for all pairs (#{}) of the kit...'), len(cset.ps))
        rpls_sel_c  =   _('Replace A&LL for all pairs of a selected kit...')
        ag.show_menu([(
    ),d(tag='rpla'  ,cap=_('Replace &all')                          ,key='Alt+A'
    ),d(tag='rpls'  ,cap=rpls_c                                     ,key='Alt+L'
    ),d(tag='arps'  ,cap=rpls_sel_c                                 ,key='Ctrl+Shift+L'
    ),d(             cap='-'
    ),d(tag='stnw'  ,cap=_('Create &new kit...')                    ,key='Ctrl+N'
    ),d(tag='prsv'  ,cap=_('&Save pattern pair to kit')             ,key='Ctrl+S'
    ),d(tag='sted'  ,cap=_('&Edit kit...')                          ,key='Ctrl+E'
    ),d(             cap=_('&Kits')                                     ,sub=nm_sets
    ),d(             cap='-'
    ),d(tag='prpr'  ,cap=_('Load previous kit pair')                ,key='Ctrl+Left'    ,en=len(cset.ps)>0
    ),d(tag='prnx'  ,cap=_('Load next kit pair')                    ,key='Ctrl+Right'   ,en=len(cset.ps)>0
    ),d(tag='stpr'  ,cap=_('Load previous kit')                     ,key='Ctrl+Shift+Left'
    ),d(tag='stnx'  ,cap=_('Load next kit')                         ,key='Ctrl+Shift+Right'
    ),d(             cap='-'
    ),d(tag='hide'  ,cap=_('Hide dialog')                           ,key='Esc'
    ),d(tag='rest'  ,cap=_('Hide dialog and restore selection &=')  ,key='Shift+Esc'
    ),d(tag='help'  ,cap=_('&Help...')                              
    ),d(tag='guid'  ,cap=_('Help - &show guide in browser')                              
    ),d(             cap='-'
    ),d(tag='fndp'  ,cap=_('Find &previous')                        ,key='Shift+Enter'
    ),d(tag='fndn'  ,cap=_('F&ind next')                            ,key='Enter'
#   ),d(tag='rprv'  ,cap=_('Replace previous')
#   ),d(tag='rnxt'  ,cap=_('Replace next')     
    ),d(             cap='-'
    ),d(tag='cpdn'  ,cap=_('Copy down: Find->Replace')            ,key='Ctrl+Down'
    ),d(tag='cpup'  ,cap=_('Copy up: Replace->Find')              ,key='Ctrl+Up'
    ),d(             cap='-'
    ),d(tag='fapp'  ,cap=_('Move to app Find dialog')               ,key='Ctrl+F'
    ),d(tag='rapp'  ,cap=_('Move to app Replace dialog')            ,key='Ctrl+R'
    ),d(             cap='-'
    ),d(             cap=_('=== Options ===')                                           ,en=False
    ),d(tag='usel'  ,cap=_('Use &selection from document')          ,ch=m.opts.usel
    ),d(tag='fitn'  ,cap=_('Auto-fit Replace pattern on start and on Next pair')    ,ch=m.opts.fitn
    ),d(tag='anxt'  ,cap=_('Load next pair after "Replace all"')    ,ch=m.opts.anxt
                    )][1:]
        ,   aid
        ,   cmd4all=m.do_acts
        )
        return d(fid='what')
       #def do_menu


    def do_keys(self, ag, key, data=''):
        pass;                   log4fun=-1
        M,m     = type(self),self
        scam    = data if data else ag.scam()
        fid     = ag.focused()
        ckey1   = str(int(chr(key))-1) if ord('1')<=key<=ord('9') else ''
        skey    = (scam,key)
        skef    = (scam,key,fid)
        pass;              #log("scam,key={}",(scam,get_const_name(key, module=cudatext_keys)))
        into    = lambda sk, scam, bgn, end: (scam, ord(bgn) if str==type(bgn) else bgn)<=sk<=(scam, ord(end) if str==type(end) else end)
        upd     = {}
        if 0:pass           #NOTE: do_keys
        elif skey==    ( 's',VK_ESCAPE):        upd=m.do_acts(ag, 'rest')       # Shift+Esc
        elif skey==    ( 'c',ord('F')):         upd=m.do_acts(ag, 'fapp')       # Ctrl+F
        elif skey==    ( 'c',ord('R')):         upd=m.do_acts(ag, 'rapp')       # Ctrl+R
        elif skey==    ( 'c',ord('S')):         upd=m.do_acts(ag, 'prsv')       # Ctrl+S
        elif skey==    ( 'c',ord('Ы')):         upd=m.do_acts(ag, 'prsv')       # Ctrl+Ы (ru)
        elif skey==    ( 'c',ord('E')):         upd=m.do_acts(ag, 'sted')       # Ctrl+E
        elif skey==    ( 'c',ord('У')):         upd=m.do_acts(ag, 'sted')       # Ctrl+У (ru)
        elif skey==    ( 'c',ord('K')):         upd=m.do_acts(ag, 'stse')       # Ctrl+K
        elif skey==    ( 'c',ord('N')):         upd=m.do_acts(ag, 'stnw')       # Ctrl+N
        elif skey==    ( 'c',ord('Т')):         upd=m.do_acts(ag, 'stnw')       # Ctrl+Т (ru)
        elif skey==    ('sc',ord('L')):         upd=m.do_acts(ag, 'arps')       # Shift+Ctrl+L
        elif skey==    ('sc',ord('Д')):         upd=m.do_acts(ag, 'arps')       # Shift+Ctrl+Д (ru)

        elif into(skey,  'c', '1','9'):         upd=m.do_acts(ag, 'stAC'+ckey1) # Ctrl+1..9
        elif into(skey, 'sc', '1','9'):         upd=m.do_acts(ag, 'stRA'+ckey1) # Ctrl+Shift+1..9

        elif skey==    ( 'c',VK_UP):            upd=m.do_acts(ag, 'cpup')       # Ctrl+Up
        elif skey==    ( 'c',VK_DOWN):          upd=m.do_acts(ag, 'cpdn')       # Ctrl+Dn
        elif skey==    ( 'c',VK_RIGHT):         upd=m.do_acts(ag, 'prnx')       # Ctrl+RT
        elif skey==    ( 'c',VK_LEFT):          upd=m.do_acts(ag, 'prpr')       # Ctrl+LF
        elif skey==    ('sc',VK_RIGHT):         upd=m.do_acts(ag, 'stnx')       # Shift+Ctrl+RT
        elif skey==    ('sc',VK_LEFT):          upd=m.do_acts(ag, 'stpr')       # Shift+Ctrl+LF

        elif skef==    (  '',VK_ENTER,'what'):  upd=m.do_acts(ag, 'fndn')       # Enter         on what
        elif skef==    ( 's',VK_ENTER,'what'):  upd=m.do_acts(ag, 'fndp')       # Shift+Enter   on what
#       elif skef==    (  '',VK_ENTER,'repl'):  upd=m.do_acts(ag, 'rpln')       # Enter         on repl
#       elif skef==    ( 's',VK_ENTER,'repl'):  upd=m.do_acts(ag, 'rplp')       # Shift+Enter   on repl

        else:   return []
        pass;                   log__('upd={}',(upd)            ,__=(log4fun,)) if _log4mod>=0 else 0
        ag.update(upd)
        pass;                   log__("break event",()          ,__=(log4fun,)) if _log4mod>=0 else 0
        return False
       #def do_keys
        
    @staticmethod
    def core_hist_ps():
        if app.app_api_version()<'1.0.347': return []
        fnd_props   = app.app_proc(app.PROC_GET_FINDER_PROP, '') 
        f_hist      = fnd_props.get('find_h', [])
        r_hist      = fnd_props.get('rep_h' , [])
        return [d(f=f, r=r, re=fnd_props['op_regex_d'], cs=fnd_props['op_case_d'], wd=fnd_props['op_word_d'])
                for f,r in zip(f_hist, r_hist)]

    def do_acts(self, ag, aid, data='', _recall=False, add_msg=False):
        """ 
            reex case word
            fapp rapp 
            rest hide help usel anxt
            cpdn cpup
            stRM stRN stAC stsw
            sets stpr stnx prpr prnx sted stnw prsv impt
            stRA stLP
            rpla rpls
        """
        M,m     = type(self),self
        pass;                   log4fun=0                       # Order log in the function
        pass;                   log("aid, data={}",(aid, data)) if log4fun else 0

        # Copy values from form to m.opts
        if not _recall:
            m.opts.update(ag.vals(['reex','case','word','what','repl']))
            m.opts.aset = ag.val('sets')

        ag.update(M.msg('')) if not add_msg else 0

        if aid in ('reex','case','word'):  # Fit focus only
            return d(fid='what')
        
        # Hide dlg
        tag     = aid
        if tag in ('fapp'
                  ,'rapp'):
            ag.opts['on_exit_focus_to_ed'] = None
            app.app_proc(app.PROC_SET_FINDER_PROP, dict(
                find_d      = ag.val('what')
            ,   rep_d       = ag.val('repl')
            ,   op_regex_d  = ag.val('reex')
            ,   op_case_d   = ag.val('case')
            ,   op_word_d   = ag.val('word')
            ))
            ag.hide()
            ed.cmd(cmds.cmd_DialogFind if tag=='fapp' else cmds.cmd_DialogReplace)
            return None
        if tag=='rest':     return (ed.set_caret(*m.ed_crts[0])     , None)[1]
        if tag=='hide':     return                                    None

        # Help
        if tag=='guid':     return (webbrowser.open_new_tab(os.path.dirname(__file__)+os.sep+'readme/batch_replacements.html'), [])[1]
        if tag=='help':     return (msg_box_ex(M.FORM_CB, M.HELP_TX), [])[1]
        if tag in ('usel'
                  ,'fitn'
                  ,'anxt'): m.opts[tag] = not m.opts[tag];  return []
        if tag=='cpdn' and \
           ag.val('what'):  return d(ctrls=d(repl=d(val=ag.val('what'))))
        if tag=='cpup'and \
           ag.val('repl'):  return d(ctrls=d(what=d(val=ag.val('repl'))))
        
        if tag    =='arps':     # Select kit to ALL
#           nms = [st.nm for st in m.opts.sets]
#           pass;               log("ikit,nms={}",(ikit,nms))
#           ikit= get_hist(M.HIST_KEY+'.prev_kit_pos', -1)
#           ikit= app.dlg_menu(app.DMENU_LIST, '\n'.join([
#                   st.nm for st in m.opts.sets
#               ])            , caption=_('Select kit to Replace ALL')
#                             , focused=ikit
#                             )
            ikit= get_hist(M.HIST_KEY+'.prev_kit_pos', -1)
            ikit= -1 if ikit is None else ikit
            nms = [st.nm for st in m.opts.sets]
            pass;              #log("ikit,nms={}",(ikit,nms))
            ikit= app.dlg_menu(app.DMENU_LIST
                              , nms
                              , caption=_('Select kit to Replace ALL')
                              , focused=ikit
                              )
            if ikit is None: return []
            set_hist(M.HIST_KEY+'.prev_kit_pos', ikit)
            return m.do_acts(ag, f'stRA{ikit}', _recall=True, add_msg=True)
        
        if(tag    =='rpls'      # Replace all from active kit
        or tag[:4]=='stRA'):    # Replace all for n-kit
            return m.work(tag, ag)

        # Change sets
        sets    = m.opts.sets
        st_desc = lambda st, sti: f('{}:"{}" (#{})', sti+1, st.nm if st.nm else M.DEF_SET, len(st.ps))
        if tag[:4]=='stRM':     # Remove
            sti = int(tag[4:])
            st  = sets[sti]
            if st.ps \
            and app.ID_YES!=msg_box(f(_('Remove kit {}'), st_desc(st, sti))
                                   , app.MB_YESNO+app.MB_ICONQUESTION):   return []
            del sets[sti]
            if not sets:
                sets.append(d(nm=M.DEF_SET, ps=[]))
            m.opts.aset = max(m.opts.aset-1, 0)
            return d(ctrls=d(sets=d(items=M.sets_items(m.opts.sets), val=m.opts.aset)))
        if tag=='stsw':         # Change positions
            ostd= {st.nm:st for st in sets}
            onms= [*ostd.keys()]
            rt,vs   = DlgAg(
                form    =d(cap=_('Re-order kits'), h=300, w=155, frame='resize')
            ,   ctrls   =d(
                    me=d(tp='memo',y=  5,x= 5   ,r=-5 ,b=-35,val=onms       ,a='b.r>' ,ro_mono_brd='0,1,1'
                  ),ok=d(tp='bttn',y=-30,x=-75  ,w= 70      ,cap=_('Save')  ,a='..--' ,on=CB_HIDE
                ))
            ,   opts    =d(negative_coords_reflect=True)).show()
            if 'ok' != rt: return []
            nnms = vs['me']
            nnms = nnms[:-1]  if app.API<349 else nnms    # :-1 - memo BUG: it adds extra EOL
            pass;               log("onms={}",(onms))
            pass;               log("nnms={}",(nnms))
            if onms==nnms:              return []               # No changes
            if set(onms)!=set(nnms):    return M.msg(_('Skip new order - kit names were not saved'))
            nsets   = [ostd[nm] for nm in nnms]
            naset   = nnms.index(sets[m.opts.aset].nm)
            m.opts.sets = nsets
            m.opts.aset = naset
            return d(ctrls=d(sets=d(items=M.sets_items(m.opts.sets), val=m.opts.aset)
                            ,stus=M.msg_d(_('Kits order was changed'))))

        if tag=='prsv':         # Add pair to set
            if not m.opts.what: return M.msg_f('what', _('Enter a non-empty Find pattern'), 'w')
            st  = sets[m.opts.aset]
            if [pr for pr in st.ps 
                if  pr.re==m.opts.reex 
                and pr.cs==m.opts.case 
                and pr.wd==m.opts.word 
                and pr.f ==m.opts.what 
                and pr.r ==m.opts.repl]:  return M.msg(_('The pair is already in the kit'), a=add_msg)
            st.ps.append(d(re=m.opts.reex, cs=m.opts.case, wd=m.opts.word, f=m.opts.what, r=m.opts.repl))
            return d(ctrls=d(sets=d(items=M.sets_items(m.opts.sets), val=m.opts.aset)
                            ,stus=M.msg_d(_('The pair was saved'), a=add_msg)))
        if(tag=='impt'          # Import 
        or tag=='stnw'          # Create
        or tag=='sted'):        # Edit name,rcw,pairs
            if app.API>=349:
                mmv_list= lambda mmv: [] if ('\n'==mmv or ''==mmv) else [mmv] if str==type(mmv) else mmv
            else:
                mmv_list= lambda mmv: [] if ('\n'==mmv or ''==mmv) else [mmv] if str==type(mmv) else mmv[:-1]     # :-1 - memo BUG: it adds extra EOL
            RCWS_H  = _('Search options as a string (any order):\r  . - RegExp\r  c - Case sensitive\r  w - Whole word')
            st      = d(nm='kit'+str(1+len(sets)), ps=M.core_hist_ps()) \
                        if tag=='impt' else \
                      d(nm='kit'+str(1+len(sets)), ps=[]) \
                        if tag=='stnw' else \
                      sets[m.opts.aset]
            rcws    = [('.' if pr.re else '')+('c' if pr.cs else '')+('w' if pr.wd else '') 
                            for pr in st.ps]
            whts    = [pr.f for pr in st.ps]
            rpls    = [pr.r for pr in st.ps]
            def on_save(ag_,name,d_=''):
                fs,rs   = map(mmv_list, ag_.vals(['whts', 'rpls']).values())
                if not len(fs)==len(rs):
                    return  M.msg_f('whts', _('Set equal number of Find/Replace patterns'), 'w')
                if whts and rpls and '' in fs:
                    return  M.msg_f('whts', _('Enter all non-empty Find patterns'), 'w')
                if ag_.val('name') in [st_.nm for st_ in sets if st_!=st]:
                    return                      M.msg_f('name', _('Set another name for kit'), 'w')
                return None # Close dlg
            fcap    = '['+M.FORM_CB+'] '+(_('New kit') if tag in ('stnw', 'impt') else 
                                        f(_('Content of kit ({})'), 1+m.opts.aset))
            ret,vals= DlgAg(
                form    =d(cap=fcap
                          ,h=260, w=700, w_max=700      # Only vert resize
                          ,frame='resize')
            ,   ctrls   =d(
            rcw_=d(tp='labl',y= 5           ,x= 5       ,w= 80  ,cap=_('. c w') ,hint=RCWS_H
          ),rcws=d(tp='memo',y=25   ,h=200  ,x= 5       ,w= 80  ,val=rcws                   ,a='b.' ,ro_mono_brd='0,1,1'
          ),wha_=d(tp='labl',y= 5           ,x=10+80    ,w=300  ,cap=_('&Find patterns:')
          ),whts=d(tp='memo',y=25   ,h=200  ,x=10+80    ,w=300  ,val=whts                   ,a='b.' ,ro_mono_brd='0,1,1'
          ),rep_=d(tp='labl',y= 5           ,x=15+80+300,w=300  ,cap=_('&Replace patterns:')
          ),rpls=d(tp='memo',y=25   ,h=200  ,x=15+80+300,w=300  ,val=rpls                   ,a='b.' ,ro_mono_brd='0,1,1'
          ),nam_=d(tp='labl',tid='okok'     ,x= 5       ,w= 80  ,cap='>'+_('&Name:')        ,a='..'    
          ),name=d(tp='edit',tid='okok'     ,x= 10+80   ,w= 80  ,val=st.nm                  ,a='..'    
          ),stus=d(tp='labl',tid='okok'     ,x= 20+80*2 ,r=-90  ,cap=''*100                 ,a='..'    
          ),oko_=d(tp='bttn',y=-30          ,x=-65      ,w= 50  ,cap=_('&ы')                ,a='..' ,on=on_save ,sto=False
          ),okok=d(tp='bttn',y=-30          ,x=-75      ,w= 70  ,cap=_('&Save')             ,a='..' ,on=on_save
                    ))
            ,   fid     ='name' if tag in ('stnw', 'impt') else 'whts'
            ,   opts    =d(negative_coords_reflect=True)
            ).show()
            if ret is None: return []
            ps,fs,rs,nm = vals.values()
            ps,fs,rs= map(mmv_list, (ps,fs,rs))
            ps      = ps[:-len(fs)] if len(ps)>len(fs) else ps+['']*(len(fs)-len(ps)) if len(ps)<len(fs) else ps
            st.nm   = nm
            st.ps   = [d(re=('.' in o), cs=('c' in o), wd=('w' in o), f=f, r=r) 
                        for o,f,r in zip(ps, fs, rs)]
            if tag in ('stnw', 'impt'):
                sets.append(st)
                m.opts.aset = len(sets)-1
            return d(ctrls=d(sets=d(items=M.sets_items(sets), val=m.opts.aset)))
        if tag=='stse':         # Edit kits
            on_help = lambda ag,name,d='':(msg_box(_(
#           on_help = lambda ag,name,d='':(msg_box_ex(_('Edit kits help'), _(
                  'Use 1+3*n lines for each kit.'
                '\r  First line for'
                '\r    n:kit name.'
                '\r  Three lines for each kit pair'
                '\r    a:attributes - "." "c" "w" - in any order,'
                '\r    f:pattern Find,'
                '\r    r:pattern Replace.'
                '\r'
                '\rFormat:'
                '\r- The order of lines with "n:", "a:", "f:", "r:" is fixed.'
                '\r- Feel free to use empty lines and some blanks before "n:", "a:", "f:", "r:".'
                '\r'
                '\rRules:'
                '\r- Empty name is correct.'
                '\r- Names must not be repeated.'
                '\r- Pattern Find must not be empty.'
                )),[])[1]
            WN,WA,WF,WR = 'n:','a:','f:','r:'
            def on_save_new_sets(ag_, name, dt=''):
                """ If dt=='' then do control before save.
                    If dt!='' then build new sets
                """
                chk     = dt==''
                kt_lns_n= (ag_.val('me') if chk else dt['me'])
                kt_lns_n= kt_lns_n[:-1] if app.API<349 else kt_lns_n    # :-1 - memo BUG: it adds extra EOL
                if not kt_lns_n:            return None if chk else []
                if kt_lns_n==kt_lns_o:      return None if chk else sets
                stsn    = []
                wait,nms,st,pr   = [WN], set(), None, None
                for nl,ln in enumerate(kt_lns_n):
                    if not ln:  continue
                    ww,ldt  = ln.lstrip()[:2], ln.lstrip()[2:]
                    if   ww not in wait:    return M.msg_f('me', _('Error: order of lines - line ')+str(1+nl), 'w')
                    if   False:pass
                    elif ww==WN \
                    and  ldt in nms:        return M.msg_f('me', _('Error: kit name repeated - ')+ldt, 'w')
                    elif ww==WN:
                        wait, st    = [WA],     d(nm=ldt, ps=[])
                        nms.add(st.nm)
                        stsn.append(st)
                    elif ww==WA:
                        wait, pr    = [WF],     d(re='.' in ldt, cs='c' in ldt, wd='w' in ldt, f='', r='')
                        st.ps.append(pr)
                    elif ww==WF \
                    and not ldt:            return M.msg_f('me', _('Error: empty Find pattern for kit - ')+st.nm, 'w')
                    elif ww==WF:
                        wait, pr.f  = [WR],     ldt
                    elif ww==WR:
                        wait, pr.r  = [WA,WN],  ldt
                if not pr.f:                return M.msg_f('me', _('Error: empty Find pattern for kit - ')+st.nm, 'w')
                if wait==[WR]:              return M.msg_f('me', _('Error: no Replace pattern for kit - ')+st.nm, 'w')
                return None if chk else stsn
                
            okts    = [ (WN+st.nm
                        ,[(' '+WA+('.' if pr.re else '')+('c' if pr.cs else '')+('w' if pr.wd else '')
                          ,' '+WF+pr.f
                          ,' '+WR+pr.r,'') for pr in st.ps
                         ],'')              for st in sets]
            kt_lns_o= [*flatten(okts)]
            rt,vs   = DlgAg(
                form    =d(cap='['+M.FORM_CB+'] '+_('Edit kits'), h=400, w=400, frame='resize')
            ,   ctrls   =d(
                    me  =d(tp='memo',y=  5    ,x= 5 ,r=-5 ,b=-35,val=kt_lns_o   ,a='b.r>'   ,ro_mono_brd='0,1,1'
                  ),stus=d(tp='labl',tid='ok' ,x= 5 ,r=-115     ,cap=''         ,a='..r>'
                  ),ok  =d(tp='bttn',y=-30    ,r=-40,w= 70      ,cap=_('&Save') ,a='..>>'   ,on=on_save_new_sets
                  ),hl  =d(tp='bttn',y=-30    ,r=-5 ,w= 30      ,cap=_('?')     ,a='..>>'   ,on=on_help
                ))
            ,   opts    =d(negative_coords_reflect=True)).show()
            if 'ok' != rt:          return []
            stsn    = on_save_new_sets(None, None, vs)
            m.opts.sets = stsn if stsn else [d(nm=M.DEF_SET, ps=[])]
            m.opts.aset = 0
            return d(ctrls=d(sets=d(items=M.sets_items(m.opts.sets), val=m.opts.aset)))

        # Use sets
        if tag=='sets':         # Changed aset
            return m.do_acts(ag, 'prnx', _recall=True)          # Auto-Load pair for loaded set
        if tag=='stpr'\
        or tag=='stnx':         # Prev/Next set
            if 1==len(sets):    return []
            m.opts.aset= (m.opts.aset + (1 if tag=='stnx' else -1)) % len(sets)
            st  = sets[m.opts.aset]
            return [m.do_acts(ag, 'prnx', _recall=True)         # Auto-Load pair for loaded set
                   ,d(ctrls=d(sets=d(val=m.opts.aset)))]
        if tag[:4]=='stAC':     # Activate by index
            sti = int(tag[4:])
            if not 0<=sti<len(sets):    return []
            m.opts.aset = sti
            return [m.do_acts(ag, 'prnx', _recall=True)         # Auto-Load pair for loaded set
                   ,d(ctrls=d(sets=d(val=m.opts.aset)))]
        
        if tag[:4]=='stLP':     # Load set and pair
            sti,pri = map(int, tag[4:].split('_'))
            if not 0<=sti<len(m.opts.sets): return []
            st  = sets[sti]
            if not 0<=pri<len(st.ps):       return []
            pr  = st.ps[pri]
            m.opts.aset = sti
            return d(ctrls=d(what=d(val=pr.f),repl=d(val=pr.r)
                            ,reex=d(val=pr.re),case=d(val=pr.cs),word=d(val=pr.wd)
                            ,sets=d(val=m.opts.aset)
                            ,stus=M.msg_d(f(_('Loaded pair {}/{}'), pri+1, len(st.ps)), a=add_msg)
                            ))
        
        if tag=='prpr'\
        or tag=='prnx':         # Prev/Next pair
            what, repl = ag.vals(['what', 'repl']).values()
            st  = sets[m.opts.aset]
            if 0==len(st.ps):    return []
            pri, off = 0, 1 if tag=='prnx' else -1
            for n,pr in enumerate(st.ps):
                if pr.f==what:
                    pri  = n            # If what       in pair then load repl
                    if pr.r==repl:
                        pri  = n+off    # If what+repl  in pair then load prev/next pair
                        break#for n,pr
            pri = pri % len(st.ps)
            pr  = st.ps[pri]
            return d(ctrls=d(what=d(val=pr.f),repl=d(val=pr.r)
                            ,reex=d(val=pr.re),case=d(val=pr.cs),word=d(val=pr.wd)
                            ,stus=M.msg_d(f(_('Loaded pair {}/{}'), pri+1, len(st.ps)), a=add_msg)
                            ))

        if(tag=='fndn' or tag=='fndp'
#       or tag=='rpln' or tag=='rplp'
        or tag=='rpla'
        ):                      # Prev/Next find/replace, replace all
            add_to_hist(m.opts.what, m.opts.whtl)   # Save as use
            add_to_hist(m.opts.repl, m.opts.rpll)   # Save as use
            return [m.work(tag, ag)
                   ,d(ctrls=d(what=d(items=m.opts.whtl)
                             ,repl=d(items=m.opts.rpll)))]
        return []
       #def do_acts
        

    def work(self, task, par=None):
        """ offer_repl fnda_locs
            stRA fndn fndp rpla rpls 
        """
        M,m         = type(self),self
        pass;                   log4fun= 0
        pass;                   log("task, par={}",(task, par)) if log4fun else 0
        if task=='offer_repl':
            what    = par
            st      = m.opts.sets[m.opts.aset]
            for pr in st.ps:
                if pr.f.startswith(what):
                    return pr.r
            return None

        ag  = par

        if( task    =='rpls'    # Replace all from active kit
        or  task[:4]=='stRA'):  # Replace all for n-kit
            sti = m.opts.aset if task=='rpls' else int(task[4:])
            if not 0<=sti<len(m.opts.sets): return []
            st      = m.opts.sets[sti]
            pass;               log("st={}",(st)) if log4fun else 0
            if not st.ps:    return M.msg(f(_('No pairs in kit "{}"'), st.nm))
            
            vtab    = lambda s:s.replace('\t', '→')
            
            rpta,cntf   = [], 0
            for np,pr in enumerate(st.ps):
                frgs= ed.action(app.EDACTION_FIND_ALL
                            , param1=pr.f
                            , param2='af' + M.st_pr_rc(pr))   # a - wrap, f - from caret
                rpta.append(f(_('{}? {}\n   {}\n   {}'), len(frgs), M.st_pr_cw(pr).ljust(5), vtab(pr.f), vtab(pr.r)))
                cntf+= len(frgs)
            if not cntf:    return M.msg(f(_('No fragments to replace with kit "{}"'), st.nm))

            need_ask    = '##SKIP-ASK##' not in st.nm

            ag_ = DlgAg(
                form    =d(cap=f(_('Replace ALL for kit ("{}")'), st.nm), h=300, w=300, frame='resize')
            ,   ctrls   =d(
                    ok=d(tp='bttn',y=-30,x=-130 ,w= 60      ,cap=_('Yes')   ,a='..>>' ,on=CB_HIDE   ,def_bt=True
                  ),ca=d(tp='bttn',y=-30,x=-65  ,w= 60      ,cap=_('No')    ,a='..>>' ,on=CB_HIDE
                  ),me=d(tp='memo',y=  5,x= 5   ,r=-5 ,b=-35,val=rpta       ,a='b.r>' ,ro_mono_brd='1,1,0'
                ))
            ,   opts    =d(negative_coords_reflect=True))
            if need_ask and \
               'ok' != ag_.show(onetime=False)[0]: return []
                    
            rpta    = []
            for np,pr in enumerate(st.ps):
                cntr= ed.action(app.EDACTION_REPLACE_ALL
                            , param1=pr.f
                            , param2=pr.r
                            , param3='af' + M.st_pr_rc(pr))   # a - wrap, f - from caret
                rpta.append(f(_('{}! {}\n   {}\n   {}'), cntr, M.st_pr_cw(pr).ljust(5), vtab(pr.f), vtab(pr.r)))
            ag_.update(form =d(cap=f(_('Results for kit ("{}")'), st.nm))
                    ,  ctrls=d(ok=d(vis=False)
                              ,ca=d(cap=_('Close'))
                              ,me=d(val=rpta)))
            if need_ask:
                ag_.show()
            return []

        if not m.opts.what: return []
        
        fops    = 'af' \
                + ('r' if m.opts.reex else '') \
                + ('c' if m.opts.case else '') \
                + ('w' if m.opts.word else '')    # a - wrap, f - from caret

        if task=='fnda_locs':
            fnda= ed.action(app.EDACTION_FIND_ALL, param1=m.opts.what, param2=fops)
            return fnda
        
        fnda    = m.work('fnda_locs', par)

        if not fnda and task=='rpla' and m.opts.anxt:
            return [M.msg(_('Not found. '))
                   ,m.do_acts(ag, 'prnx', _recall=True, add_msg=True)]
        elif not fnda:
            return M.msg(_('Not found'))
        
        fact    = None
        pars    = None
        if False:pass
        elif task=='fndn' \
        or   task=='fndp':
            fact= app.EDACTION_FIND_ONE
            pars= d(param1=m.opts.what
                   ,param2=fops+('b' if task=='fndp' else ''))
        elif task=='rpla':
            fact= app.EDACTION_REPLACE_ALL
            pars= d(param1=m.opts.what, param2=m.opts.repl
                   ,param3=fops)

        pass;                   log(f"fact={fact} pars={pars}") if log4fun else 0
        rsp     = ed.action(fact, **pars)
        pass;                   log(f"rsp={rsp}") if log4fun else 0
        
        if False:pass
        elif (task=='fndn' or    task=='fndp' 
#       or    task=='rpln' or    task=='rplp'
        ):
            ed.set_caret(*rsp)
            fpos= fnda.index(rsp)
            return M.msg(f'{fpos+1}({len(fnda)})')
            return []
        elif task=='rpla' and m.opts.anxt:
            return [M.msg(f(_('Replaces made: {}. '), len(fnda)))
                   ,m.do_acts(ag, 'prnx', _recall=True, add_msg=True)]
        elif task=='rpla': # and not m.opts.anxt
            return  M.msg(f(_('Replaces made: {}'), len(fnda)))
       #def work

   #class RiL
theRiL          = RiL()                                         # Single obj

def dlg_replace_in_lines():                                     #NOTE: dlg_replace_in_lines
    theRiL.show()   # new!
   #def dlg_replace_in_lines
def kit_replace_in_lines():
    theRiL.do_acts(None, 'arps', _recall=True, add_msg=True)
   #def kit_replace_in_lines



class FiL:
    FORM_C  =   _('Find in Lines')
    HELP_C  = _('''
• Search "in Lines" starts immediately (if focus in the left edit) or on Enter or Shift+Enter (if focus in the right edit).
• A found fragment after first caret will be selected.
• All found fragments are remembered and dialog can jump over them by [Shift+]Enter or by menu commands.
• Ctlr+Right (or Alt+Right) copies text from the left edit to the right.
• Ctlr+Left (or Alt+Left) copies text from the right edit to the left.
• Option ".*" (regular expression) allows to use Python reg.ex. See "docs.python.org/3/library/re.html".
• Option "w" (whole words) is ignored if entered string contains not a word.
• If option "Instant search" (in menu) is tuned on, search result will be updated on start and after each change of pattern.
• Command "Restore initial selection" (Shift+Esc) restores only first of initial carets.
• Ctrl+F (or Ctrl+R) calls appication dialog Find (or Replace).
    ''').strip()

    # To select found fragment
    select_frag = lambda frag_inf:  ed.set_caret(*frag_inf)
        
    # To fit pattern to find
    compile_pttn= lambda    pttn_s, reex, case, word: re.compile(
                            pttn_s          if reex else
                      r'\b'+pttn_s+r'\b'    if word and re.match('^\w+$', pttn_s) else
                  re.escape(pttn_s)
                        ,   0 if case else re.I)
        
    ed_crts     = None                                          # Carets at start
    opts        = None

    ag          = None                                          # Nonmodal obj

    what        = ''                                            # String to search 
    prev_wt     = ''                                            # Prev what
    ready_l     = []                                            # [(row,col_bgn,col_end)]
    ready_p     = -1                                            # pos in ready_l
    
    last_awht   = 'what'
    
    @staticmethod
    def msg_(msg=None):
        msg =(msg                                                       if msg else
              f('{}/{}', 1+FiL.ready_p, len(FiL.ready_l))               if FiL.ready_l else
              f(_('Left input: at least {} chars. Right input: ENTER.'), FiL.opts['insm'])
             )
        msg = f('{}: {}' , FiL.FORM_C, msg)                             if FiL.opts['dock'] else \
              f('{} ({})', FiL.FORM_C, msg)
        return msg
       #def msg_
    @staticmethod
    def msg_upd(msg=None, fid='what'):
        msg = FiL.msg_(msg)
        return {'ctrls':{'mess':{'cap':msg}},'fid':fid}                 if FiL.opts['dock'] else \
               {'form':         {'cap':msg} ,'fid':fid}
       #def msg_upd
        

    def show(self):
        M,m     = type(self),self
        pass;                   log4fun=0                       # Order log in the function

        FiL.ed_crts = ed.get_carets()                           # Carets at start/activate
        pass;                  #log__('hist={}',(get_hist('find.find_in_lines'))  ,__=(log4fun,_log4mod))
        FiL.opts    = d(reex=False,case=False,word=False
                    ,   hist=[]
                    ,   usel=False
                    ,   dock='',dock_ww=300
                    ,   nmdl=False
                    ,   inst=False,insm=3
                    ,   pfid='what')                            # Default options
        FiL.opts.update(get_hist('find.find_in_lines', FiL.opts))
        pass;                  #log("FiL.opts={}",(FiL.opts))

        FiL.ag      = FiL.ag if (FiL.ag and FiL.ag.islived()) else None
        pass;                   log__("FiL.what={}",(FiL.what)  ,__=(log4fun,_log4mod))

        FiL.ready_l = []
        FiL.ready_p = -1
        FiL.prev_wt = ''                                        # To refind 

        awht    = FiL.opts['pfid'] if FiL.opts['pfid'] in ('whti', 'what') else 'what'
        what    =(ed.get_text_sel()
                    if FiL.opts['usel'] else #and ed.get_text_sel() else
                  FiL.what)
        what    = '' if '\r' in what or '\n' in what else what
        
        pass;                   log__("FiL.ag={}",(FiL.ag)  ,__=(log4fun,_log4mod))
        if FiL.ag:
            ##??
            FiL.ag.activate()
            FiL.ag.update(d(vals=d(whti=what if awht=='whti' else ''
                                  ,what=what if awht=='what' else '')))
            pass;               log__('FiL.prev_wt, len(FiL.ready_l)={}',(FiL.prev_wt, len(FiL.ready_l))  ,__=(log4fun,_log4mod))
            return FiL.ag.update(self.do_find(FiL.ag, 'find', awht))                 # To refind 
        
        pass;                  #log__('###',()  ,__=(log4fun,_log4mod))

        dock    = FiL.opts['dock']
        wtwd    = FiL.opts['dock_ww']   if dock else 105
        mswd    = 150                   if dock else 0
        menx    = 5+114+5+wtwd+5+wtwd+5
#       menx    = 5+114+5+105 +5+wtwd+5
        msg     = FiL.msg_()
        ag      = DlgAg(
            form    =dict(cap=msg, w=5+114+5+wtwd+5+wtwd+39+5+5
#           form    =dict(cap=msg, w=5+114+5+105 +5+wtwd+39+5+5
                         ,h=38, h_max=38                        # Only horz resize
                         ,on_key_down=m.do_key_down
                         ,on_resize=m.on_resize
                         ,frame='resize'
                         )
        ,   ctrls   =[0
      ,('find',d(tp='bttn'  ,y=0        ,x=-99          ,w=11   ,cap=''     ,sto=False  ,def_bt='1'         ,on=m.do_find   ))  # Enter
      ,('reex',d(tp='chbt'  ,tid='what' ,x=5            ,w=38   ,cap='&.*'  ,hint=_('Regular expression')   ,on=m.do_attr   ))  # &.
      ,('case',d(tp='chbt'  ,tid='what' ,x=5+ 38        ,w=38   ,cap='&aA'  ,hint=_('Case sensitive')       ,on=m.do_attr   ))  # &a
      ,('word',d(tp='chbt'  ,tid='what' ,x=5+ 76        ,w=38   ,cap='"&w"' ,hint=_('Whole words')          ,on=m.do_attr   ))  # &w
      ,('whti',d(tp='edit'  ,tid='what' ,x=5+114+5      ,w=wtwd                                             ,on=m.do_find   ))  # 
#     ,('whti',d(tp='edit'  ,tid='what' ,x=5+114+5      ,w=105                                              ,on=m.do_find   ))  # 
      ,('what',d(tp='cmbx'  ,y  =5      ,x=5+114+10+wtwd,w=wtwd ,items=FiL.opts['hist']                                     ,_a=''   if dock else 'r>'   ))  # 
#     ,('what',d(tp='cmbx'  ,y  =5      ,x=5+114+115    ,w=wtwd ,items=FiL.opts['hist']                                     ,_a=''   if dock else 'r>'   ))  # 
      ,('menu',d(tp='bttn'  ,tid='what' ,x=menx         ,w=38   ,cap='&='               ,on_menu=m.do_menu  ,on=m.do_menu   ,a=''   if dock else '>>'   ))  # &=
      ,('mess',d(tp='labl'  ,tid='what' ,x=menx+39+5    ,w=mswd ,cap=msg                                                    ,a='r>' if dock else ''     ))  # 
                    ][1:]
        ,   fid     =FiL.opts['pfid']
#       ,   fid     ='what'
        ,   vals    =d(**{k:FiL.opts[k] for k in ('reex','case','word')}
                        , whti=what if awht=='whti' else ''
                        , what=what if awht=='what' else '')
       #,   opts    ={}
        )
        pass;                  #ag.gen_repro_code('repro_dlg_fil.py')
        
        pass;                  #log__("FiL.opts[inst] and what={}",(FiL.opts['inst'], what)  ,__=(log4fun,_log4mod))
        if FiL.opts['pfid']=='whti' and what:
#       if FiL.opts['inst'] and what:
            ag.update(m.do_find(ag, 'find'))

        FiL.ag  = ag if FiL.opts['nmdl'] or FiL.opts['dock'] else None
        pass;                   log__("FiL.ag={}",(FiL.ag)  ,__=(log4fun,_log4mod))

        ag.dock(FiL.opts['dock'])
        ag.show( on_exit=self.on_exit
                ,modal=not (FiL.opts['nmdl'] or FiL.opts['dock'])
                )
       #def show


    def on_resize(self, ag, key, data=''):
        xi, xm  = ag.cattr('whti', 'x'), ag.cattr('menu', 'x')
        w2      = (xm - xi - 10) // 2
        FiL.opts['dock_ww'] = w2
        return d(ctrls=d(whti=d(x=xi     , w=w2),
                         what=d(x=xi+w2+5, r=xm-5)))
       #def on_resize


    def do_find(self, ag, aid, data=''):
        pass;                   log4fun=0                       # Order log in the function
        fid     = ag.focused()
        pass;                   log__('aid, data, fid={}',(aid, data, fid)  ,__=(log4fun,_log4mod))
        # What/how will search
        prnx    = 'prev' if aid=='prev' else 'next'
        crt     = ed.get_carets()[0][:]                         # Current first caret (col,row, col?,row?)
        min_rc  = (crt[1], crt[0])  if crt[2]==-1 else  min((crt[1], crt[0]), (crt[3], crt[2]))
        max_rc  = (crt[1], crt[0])  if crt[2]==-1 else  max((crt[1], crt[0]), (crt[3], crt[2]))

#       awht    = data if data else 'whti' if aid=='whti' else 'what'
        awht    =(data      if data                             else 
                  'whti'    if aid=='whti' and FiL.opts['dock'] else    # fix to core bug: fid is not correct for docked form
                  fid       if fid in ('whti', 'what')          else 
                  'whti'    if aid=='whti'                      else 
                  'what'
                 )
#       awht    = data if data else 'whti' if ag.focused()=='whti' else 'what'
        FiL.last_awht   = awht
        what    = ag.val(awht)

        pass;                   log__('what, FiL.prev_wt, len(FiL.ready_l)={}',(what, FiL.prev_wt, len(FiL.ready_l))  ,__=(log4fun,_log4mod))
        if FiL.prev_wt==what and FiL.ready_l:                   # Jump to next/prev
            if 1==len(FiL.ready_l):
                pass;           log__('no jump for single',()  ,__=(log4fun,_log4mod))
                return  d(fid=awht)
            FiL.ready_p = (FiL.ready_p + (-1 if aid=='prev' else 1)) % len(FiL.ready_l)
            pass;               log__('jump to {}',(FiL.ready_p)  ,__=(log4fun,_log4mod))
            FiL.select_frag(FiL.ready_l[FiL.ready_p])
            return FiL.msg_upd(fid=awht)
        FiL.prev_wt = what
        FiL.what    = what
        
        FiL.opts.update(ag.vals(['reex','case','word']))
        
        if not what:                                            # Nothing to show
            FiL.ready_l, FiL.ready_p    = [], -1
            pass;               log__('no what',()  ,__=(log4fun,_log4mod))
            return                      FiL.msg_upd(fid=awht)
        if  awht=='whti'                and \
            len(what)<FiL.opts['insm']  and \
                  not FiL.opts['reex']:                         # Not ready to find     reex??
            FiL.ready_l, FiL.ready_p    = [], -1
            pass;               log__('not ready',()  ,__=(log4fun,_log4mod))
            return                      FiL.msg_upd(fid=awht)
        
        up_hist = []
        if awht=='what':
            FiL.opts['hist']= add_to_hist(what, FiL.opts['hist'])
            up_hist = [d(ctrls=d(what=d(items=FiL.opts['hist'])))]
        # New search
        FiL.ready_l = []
        FiL.ready_p = -1
        pttn_r  = None
        try:
            pttn_r  = FiL.compile_pttn(what, FiL.opts['reex'], FiL.opts['case'], FiL.opts['word'])
        except Exception as ex:
            return up_hist+[FiL.msg_upd(str(ex), fid=awht)]

        pass;                   log__('FiL.ready_p,min_rc,max_rc={}',(FiL.ready_p,min_rc,max_rc)  ,__=(log4fun,_log4mod))
        FiL.ready_p = -1
        for row in range(ed.get_line_count()):
            line    = ed.get_text_line(row)
            mtchs   = pttn_r.finditer(line)
            if not mtchs:  continue
            for mtch in mtchs:
                fnd_bgn = mtch.start()
                fnd_end = mtch.end()
                if  FiL.ready_p==-1: 
                    FiL.ready_p = ( len(FiL.ready_l)
                            if                  FiL.ready_p==-1 and                         # Near after caret
                                row>min_rc[0]  or row==min_rc[0] and fnd_bgn>=min_rc[1]
                            or prnx=='next' and FiL.ready_p==-1 and                         # Need next and no yet
                                (row>max_rc[0] or row==max_rc[0] and fnd_bgn>max_rc[1])     # At more row or at more col in cur row
                            or prnx=='prev'                     and                         # Need prev
                                (row<min_rc[0] or row==min_rc[0] and fnd_end<min_rc[1])     # At less row or at less col in cur row
                            else FiL.ready_p)
                FiL.ready_l+= [(fnd_end, row, fnd_bgn, row)]
        pass;                  #log__('FiL.ready_p={}',(FiL.ready_p)  ,__=(log4fun,_log4mod))
        pass;                  #log__('FiL.ready_l={}',(FiL.ready_l)  ,__=(log4fun,_log4mod))
        FiL.ready_p = max(0, FiL.ready_p) if FiL.ready_l else -1
        pass;                  #log__('FiL.ready_p={}',(FiL.ready_p)  ,__=(log4fun,_log4mod))
        # Show results
        if FiL.ready_l:
#           if aid=='find' and 'stay' in data:
#               FiL.ready_p = (FiL.ready_p-1) % len(FiL.ready_l)
            pass;              #log__('show rslt FiL.ready_p={}',(FiL.ready_p,)  ,__=(log4fun,_log4mod))
            FiL.select_frag(FiL.ready_l[FiL.ready_p])
        pass;                   log__('FiL.ready_p={}/{}',FiL.ready_p,len(FiL.ready_l)  ,__=(log4fun,_log4mod))
        pass;                   log__('msg_upd()={}',FiL.msg_upd()  ,__=(log4fun,_log4mod))
        return up_hist+[FiL.msg_upd('0' if not FiL.ready_l else None, fid=awht)]
       #def do_find
        

    def do_menu(self, ag, aid, data=''):
        def wnen_menu(ag, tag):
            # Commands
            if tag=='help':             return (msg_box(FiL.HELP_C)                 , [])[1]
            if tag in ('prev','next'):  return self.do_find(ag, tag, FiL.last_awht)
            if tag=='natf':             return (self.switch_to_dlg(ag, 'find')      , None)[1]
            if tag=='natr':             return (self.switch_to_dlg(ag, 'repl')      , None)[1]
            if tag=='rest':             return (ed.set_caret(*FiL.ed_crts[0])       , None)[1]
            if tag=='hide':             return                                        None
            # Options
            if tag=='insm':
                insm    = str(FiL.opts['insm'])
                while True:
                    insm        = app.dlg_input(_('Instant search - minimal length'), insm)
                    if not insm:        return []
                    if re.match(r'^\d+$', insm): break
                FiL.opts['insm']= int(insm)
                return FiL.msg_upd()
            tohide  = '.' in tag
            tag     = tag.strip('.')
            if tag in ('usel'
                      ,'nmdl'):
                FiL.opts[tag]   = not FiL.opts[tag]
            if tag in ('dckt'
                      ,'dckb'):
                FiL.opts['dock']= 't' if tag=='dckt' and FiL.opts['dock']!='t' else \
                                  'b' if tag=='dckb' and FiL.opts['dock']!='b' else \
                                  ''
                FiL.opts['dock_ww'] = ag.cattr('what', 'w')
            if tohide:
                ag.hide()
                return None
            return []
           #def wnen_menu
        insm_c  = f(_('&Minimal length of instant-search (left) field: {}...'), FiL.opts['insm'])
        modl    = not (FiL.opts['nmdl'] or FiL.opts['dock'])
        ag.show_menu([(
    ),d(tag='hide'  ,cap=_('Hide dialog &=')                                ,key=('Esc' if modl else '')
    ),d(tag='rest'  ,cap=_('Hi&de dialog and restore selection')            ,key='Shift+Esc'
    ),d(tag='help'  ,cap=_('&Help...')                                      
    ),d(             cap='-'
    ),d(tag='prev'  ,cap=_('Find &previous')                                ,key='Shift+Enter'
    ),d(tag='next'  ,cap=_('F&ind next')                                    ,key='Enter'
    ),d(             cap='-'
    ),d(tag='natf'  ,cap=_('Move to app &Find dialog')                      ,key='Ctrl+F'
    ),d(tag='natr'  ,cap=_('Move to app &Replace dialog')                   ,key='Ctrl+R'
    ),d(             cap='-'
    ),d(             cap=_('=== Options ===')                                           ,en=False
    ),d(tag='usel'  ,cap=_('Use &selection from document')          ,ch=FiL.opts['usel']
    ),d(tag='insm'  ,cap=insm_c
    ),d(             cap='-'
    ),d(tag='nmdl.' ,cap=_('Work in non-modal mod&e (close dialog)'),ch=FiL.opts['nmdl'],en=FiL.opts['dock']==''    # '.' to hide
    ),d(tag='dckt.' ,cap=_('Dock to window &top (close dialog)')    ,ch=FiL.opts['dock']=='t'                       # '.' to hide
    ),d(tag='dckb.' ,cap=_('Dock to window &bottom (close dialog)') ,ch=FiL.opts['dock']=='b'                       # '.' to hide
                    )][1:]
        ,   aid
        ,   cmd4all=wnen_menu                               # Set cmd=wnen_menu for all nodes
        )
        return d(fid='what')
       #def do_menu
        

    def on_exit(self, ag):
        pass;                   log__("FiL.ag={}",(FiL.ag)  ,__=(_log4mod,))
        FiL.opts['pfid']    = ag.focused()
        pass;                  #log("FiL.opts={}",(FiL.opts))
        set_hist('find.find_in_lines', {**FiL.opts, **ag.vals(['reex','case','word'])})


    def do_key_down(self, ag, key, data=''):
        scam    = data if data else ag.scam()
        pass;              #log("scam,key={}",(scam,get_const_name(key, module=cudatext_keys)))
        if 0:pass
        elif (scam,key)==('s',VK_ENTER):                        # Shift+Enter
            ag.update(self.do_find(ag, 'prev'))
        elif (scam,key)==('' ,VK_ESCAPE) and FiL.opts['nmdl']:  # Esc
            pass;              #log("",())
            ed.focus()
            return False                                        # Dont close dlg
#       elif (scam,key)==('' ,VK_ESCAPE):                       # Esc
        elif (scam,key)==('s',VK_ESCAPE):                       # Shift+Esc
            ed.set_caret(*FiL.ed_crts[0])
            ag.hide()
        elif (scam,key)==('c',ord('F')) or \
             (scam,key)==('c',ord('R')):                        # Ctrl+F or Ctrl+R
            self.switch_to_dlg(ag, 'find' if key==ord('F') else 'repl')
        elif (scam,key)==('c',VK_RIGHT) or \
             (scam,key)==('a',VK_RIGHT):                        # Shift+Rt or Alt+Rt
            l_pttn  = ag.val('whti')
            if not l_pttn:  return []
            ag.update(d(fid='what', ctrls=d(what=d(val=l_pttn))))
            ag.update(self.do_find(ag, 'what'))
        elif (scam,key)==('c',VK_LEFT) or \
             (scam,key)==('a',VK_LEFT):                         # Shift+Lf or Alt+Lf
            r_pttn  = ag.val('what')
            if not r_pttn:  return []
            ag.update(d(fid='whti', ctrls=d(whti=d(val=r_pttn))))
            ag.update(self.do_find(ag, 'whti'))
        else: return [] # Nothing
        return False    # Stop event
       #def do_key_down
        

    def do_attr(self, ag, aid, data=''):
        " State of re/word/case will be saved on exit. Need only new search. "
        FiL.prev_wt = ''                                        # To refind 
        return self.do_find(ag, 'find', FiL.last_awht)          # To refind 
#       return self.do_find(ag, 'find', 'stay')                 # To refind 
       #def do_attr


    def switch_to_dlg(self, ag, dlg='find'):
        ag.opts['on_exit_focus_to_ed'] = None
        if app.app_api_version()>='1.0.248':
            app.app_proc(app.PROC_SET_FINDER_PROP, d(
                find_d      = ag.val('what' if FiL.last_awht=='what' else 'whti')
            ,   op_regex_d  = ag.val('reex')
            ,   op_case_d   = ag.val('case')
            ,   op_word_d   = ag.val('word')
            ))
        ag.hide()
        ed.cmd(cmds.cmd_DialogFind if dlg=='find' else cmds.cmd_DialogReplace)
       #def switch_to_dlg

   #class FiL
theFiL          = FiL()                                         # Single obj

def dlg_find_in_lines():                                        #NOTE: dlg_find_in_lines
    theFiL.show()   # new!
   #def dlg_find_in_lines



def find_cb_by_cmd(updn):
    if app.app_api_version()<'1.0.182':  return app.msg_status(_("Need update CudaText"))
    clip    = app.app_proc(app.PROC_GET_CLIP, '')
    if ''==clip:    return
    clip    = clip.replace('\r\n', '\n').replace('\r', '\n')    ##??

    fpr         = None
    user_opt    = None
    # c - Case, r - RegEx,  w - Word,  f - From-caret,  a - Wrapp,  b - Back
    find_opt= 'f'
    if app.app_api_version()>='1.0.248':
        fpr     = app.app_proc(app.PROC_GET_FINDER_PROP, '')
        find_opt= find_opt + ('c' if ('op_case_d' in fpr and fpr['op_case_d'] or fpr['op_case']) else '')
        find_opt= find_opt + ('w' if ('op_word_d' in fpr and fpr['op_word_d'] or fpr['op_word']) else '')
        find_opt= find_opt + ('a' if ('op_wrap_d' in fpr and fpr['op_wrap_d'] or fpr['op_wrap']) else '')
    else:
        user_opt= app.app_proc(app.PROC_GET_FIND_OPTIONS, '')   # Deprecated
        find_opt= find_opt + ('c' if 'c' in user_opt else '')   # As user: Case
        find_opt= find_opt + ('w' if 'w' in user_opt else '')   # As user: Word
        find_opt= find_opt + ('a' if 'a' in user_opt else '')   # As user: Wrap

    ed.cmd(cmds.cmd_FinderAction, C1.join([]
        +['findprev' if updn=='up' else 'findnext']
        +[clip]
        +['']
        +[find_opt]
    ))
    if app.app_api_version()>='1.0.248':
        fpr['find']     = clip
        fpr['find_d']   = clip
        app.app_proc(app.PROC_SET_FINDER_PROP, fpr)
    else:
        app.app_proc(app.PROC_SET_FIND_OPTIONS, user_opt)       # Deprecated
   #def find_cb_by_cmd


def replace_all_sel_to_cb():
    if app.app_api_version()<'1.0.182':  return app.msg_status(_("Need update CudaText"))
    crts    = ed.get_carets()
    if len(crts)>1: return app.msg_status(_("{} doesn't work with multi-carets").format(_('Command')))
    seltext = ed.get_text_sel()
    if not seltext: return app.msg_status(_('No selected text to replace'))
    clip    = app.app_proc(app.PROC_GET_CLIP, '')
    if not clip:    return app.msg_status(_('No clipped text to replace'))

    fpr         = None
    user_opt    = None
    # c - Case, r - RegEx,  w - Word,  f - From-caret,  a - Wrapp,  b - Back
    find_opt= 'a'
    if app.app_api_version()>='1.0.248':
        fpr     = app.app_proc(app.PROC_GET_FINDER_PROP, '')
        find_opt= find_opt + ('c' if ('op_case_d' in fpr and fpr['op_case_d'] or fpr['op_case']) else '')
        find_opt= find_opt + ('w' if ('op_word_d' in fpr and fpr['op_word_d'] or fpr['op_word']) else '')
    else:
        user_opt= app.app_proc(app.PROC_GET_FIND_OPTIONS, '')   # Deprecated
        find_opt= find_opt + ('c' if 'c' in user_opt else '')   # As user: Case
        find_opt= find_opt + ('w' if 'w' in user_opt else '')   # As user: Word
    ed.lock()
    pass;                      #log__('seltext,clip,find_opt={!r}',(seltext,clip,find_opt)  ,__=(log4fun,_log4mod))
    ed.cmd(cmds.cmd_FinderAction, C1.join([]
        +['repall']
        +[seltext]
        +[clip]
        +[find_opt]  # a - wrapped
    ))
    ed.unlock()
    if app.app_api_version()>='1.0.248':
        app.app_proc(app.PROC_SET_FINDER_PROP, fpr)
    else:
        app.app_proc(app.PROC_SET_FIND_OPTIONS, user_opt)       # Deprecated
   #def replace_all_sel_to_cb


def add_carets_for_rect():
    c, r, c1, r1 = ed.get_carets()[0]
    rsp, vals   = DlgAg(
        form    =d(cap =_('Set carets aligned as column'), w=235, h=210)
    ,   ctrls   =d(
      lin_=d(tp='labl',tid='line'   ,x=5  ,w=140  ,cap='>'+_('At &line:')           # &L
    ),line=d(tp='sped',y  =  5      ,x=5+140+5  ,w= 80  ,val=r+1    ,min_max_inc=f'1,{ed.get_line_count()},1'
    ),col_=d(tp='labl',tid='colm'   ,x=5  ,w=140  ,cap='>'+_('At &column:')         # &C
    ),colm=d(tp='sped',y  = 40      ,x=5+140+5  ,w= 80  ,val=c+1    ,min_max_inc=f'1,200,1'
    ),heh_=d(tp='labl',tid='heht'   ,x=5  ,w=140  ,cap='>'+_('&Height in lines:')   # &H
    ),heht=d(tp='sped',y  = 75      ,x=5+140+5  ,w= 80  ,val=2      ,min_max_inc=f'1,{ed.get_line_count()},1'
    ),wid_=d(tp='labl',tid='widt'   ,x=5  ,w=140  ,cap='>'+_('&Width of selection:')# &W
    ),widt=d(tp='sped',y  =115      ,x=5+140+5  ,w= 80  ,val=0      ,min_max_inc=f'0,200,1'
    ),apnd=d(tp='chck',y  =145      ,x=5  ,w= 200       ,val=False  ,cap=_('&Keep existing caret(s)')   # &K

    ),cncl=d(tp='bttn',y=-35        ,r=-5-80-5  ,w= 80  ,cap=_('Cancel')        ,on=CB_HIDE #   
    ),okok=d(tp='bttn',y=-35        ,r=-5       ,w= 80  ,cap=_('OK'),def_bt='1' ,on=CB_HIDE #   
            ))
        ,   fid     = 'heht'
    ,   opts    =d(negative_coords_reflect=True)
        ).show()
    if rsp!='okok':   return 
    x = vals['colm'] - 1
    y = vals['line'] - 1
    w = vals['widt']
    h = vals['heht']
    clear = not vals['apnd']

    if clear:
        ed.set_caret(0, 0, 0, 0, app.CARET_DELETE_ALL)
    for i in range(h):
        if w:   ed.set_caret(x+w, y+i, x, y+i, app.CARET_ADD)
        else:   ed.set_caret(x,   y+i, -1, -1, app.CARET_ADD)

    ed.action(app.EDACTION_UPDATE)
    app.msg_status(f(_('Added {} caret(s)'), h))
   #def add_carets_for_rect


def convert_sel_to_column():
    '''
    Convert single multi-line selection to column selection
    '''
    crts    = ed.get_carets()
    if len(crts)>1:
        return app.msg_status(_("{} doesn't work with multi-carets").format(_('Command')))
    x1, y1, x2, y2 = crts[0]
    if y2<0 or y1==y2:
        return app.msg_status(_("{} works with multiline selection").format(_('Command')))
    # sort coords
    if (y1, x1)>(y2, x2):
        x1, y1, x2, y2 = x2, y2, x1, y1

    col1 = 0
    col2 = x2
    for y in range(y1, y2):
        col2 = max(col2, len(ed.get_text_line(y)))
                
    ed.set_sel_rect(col1, y1, col2, y2)
    app.msg_status(_('Converted to column block'))
   #def convert_sel_to_column
   
def convert_reverse_selection():
    " Author: github.com/Alexey-T "
    carets = ed.get_carets()
    rng = []

    for x1, y1, x2, y2 in carets:
        if y2>=0:
            if (y1, x1)>(y2, x2):
                x1, y1, x2, y2 = x2, y2, x1, y1
                    
            if y1==y2:
                rng.append((x1, y1, x2))
            else:
                rng.append((x1, y1, len(ed.get_text_line(y1))))
                for y in range(y1+1, y2):
                    rng.append((0, y, len(ed.get_text_line(y))))
                rng.append((0, y2, x2))

    # delete empty fragments
    rng = [r for r in rng if r[2]>r[0]]

    for x1, y1, x2 in reversed(rng):                
        s = ed.get_text_substr(x1, y1, x2, y1)
        ed.replace(x1, y1, x2, y1, s[::-1])

    n = len(rng)
    if n==0:
        app.msg_status(_('Make selection first'))
    elif n==1:                
        app.msg_status(_('Reversed 1 fragment'))
    elif n>1:
        app.msg_status(f(_('Reversed {} fragments'), n))
   #def convert_reverse_selection

data4_align_in_lines_by_sep = ''
def align_in_lines_by_sep():
    ''' Add spaces for aline text in some lines
        Example. Start lines
            a= 0
            b
            c  = 1
        Aligned lines
            a  = 0
            b
            c  = 1
    '''
    global data4_align_in_lines_by_sep
    crts    = ed.get_carets()
    if len(crts)>1:
        return app.msg_status(_("{} doesn't work with multi-carets").format(_('Command')))
    (cCrt, rCrt
    ,cEnd, rEnd)    = crts[0]
    if rEnd==-1 or rEnd==rCrt:
        return app.msg_status(_("{} works with multiline selection").format(_('Command')))
    spr     = app.dlg_input(_('Enter separator string'), data4_align_in_lines_by_sep)
    spr     = '' if spr is None else spr.strip()
    if not spr:
        return # Esc
    data4_align_in_lines_by_sep    = spr
    line1, line2 = ed.get_sel_lines() # Alexey: works good even if last line don't have EOL
    line2len = len(ed.get_text_line(line2))
    ls_txt  = ed.get_text_substr(0, line1, line2len, line2)
    if spr not in ls_txt:
        return app.msg_status(_("No separator '{}' in selected lines").format(spr))
    lines   = ls_txt.splitlines()
    ln_poss = [(ln, ln.find(spr)) for ln in lines]
    max_pos =    max([p for (l,p) in ln_poss])
    if max_pos== min([p if p>=0 else max_pos for (l,p) in ln_poss]):
        return app.msg_status(_("Text change not needed"))
    nlines  = [ln       if pos==-1 or max_pos==pos else
               ln[:pos]+' '*(max_pos-pos)+ln[pos:]
               for (ln,pos) in ln_poss
              ]
    ed.replace_lines(line1, line2, nlines)
    ed.set_caret(line2len, line2, 0, line1)
   #def align_in_lines_by_sep


def reindent():
    if app.app_api_version()<'1.0.187': return app.msg_status(_('Need update application'))
    crts    = ed.get_carets()
    if len(crts)>1:
        return app.msg_status(_("{} doesn't work with multi-carets").format(_('Command')))
    (cCrt, rCrt
    ,cEnd, rEnd)    = crts[0]
    cEnd, rEnd      = (cCrt, rCrt) if rEnd==-1 else (cEnd, rEnd)
    (rSelB, cSelB), \
    (rSelE, cSelE)  = apx.minmax((rCrt, cCrt), (rEnd, cEnd))
    rSelE           = rSelE - (1 if 0==cSelE else 0)

    first_s     = ed.get_text_line(rSelB)
    ed_tab_sp   = apx.get_opt('tab_spaces', False)
    ed_tab_sz   = apx.get_opt('tab_size'  , 8)
    ed_blanks   = '.'*ed_tab_sz
    old_s       = 't' if first_s.startswith('\t')   else ed_blanks
    new_s       = 't' if old_s!='t' else ed_blanks
    fill_h      = _('''
To specify two/four/eight blanks enter
    these blanks
or
    "2b"/"4b"/"8b"
or
    ".."/"...."/"........" (dots).
To specify TAB enter "t".
                  ''').strip()
    def parse_step(step):
        if step in 't\t':               return '\t'
        if not step.replace(' ', ''):   return step
        if step[0].isdigit():           return ' '*int(step[0])
        return ''
    vals        = dict(olds=old_s
                      ,news=new_s)
    
    def acts(ag, cid, data=''):
        vals    = ag.vals()
        if ''==vals['olds'] or vals['olds'][0] not in ' .t2345678':
            msg_box(_('Fill "Old step".\n\n')+fill_h)
            return d(fid='olds')
        if ''==vals['news'] or vals['news'][0] not in ' .t2345678':
            msg_box(_('Fill "New step".\n\n')+fill_h)
            return d(fid='news')
        ag.hide(cid)
       #def acts
    ag  = DlgAg(
            form=d(
                cap =f(_('Reindent selected lines ({})'), rSelE-rSelB+1)
            ,   w   =245
            ,   h   =120
            )
        ,   ctrls=[0
    ,('old_',d(tp='labl',tid='olds' ,x=5        ,w=150  ,cap='>'+_('&Old indent step:') ,hint=fill_h)) # &o
    ,('olds',d(tp='edit',y=10       ,x=5+150+5  ,w= 80                                              )) # 
    ,('new_',d(tp='labl',tid='news' ,x=5        ,w=150  ,cap='>'+_('&New indent step:') ,hint=fill_h)) # &n
    ,('news',d(tp='edit',y=50       ,x=5+150+5  ,w= 80                                              ))
    ,('okok',d(tp='bttn',y=90       ,x=245-170-5,w= 80  ,cap=_('OK')                    ,def_bt='1' ,on=acts)) #   
    ,('cncl',d(tp='bttn',y=90       ,x=245-80-5 ,w= 80  ,cap=_('Cancel')                            ,on=CB_HIDE))
            ][1:]
        ,   vals    = vals
        ,   fid     = 'olds'
        )
    aid, vals   = ag.show()
    if aid!='okok': return 
    old_s   = parse_step(vals['olds'].replace('.', ' '))
    new_s   = parse_step(vals['news'].replace('.', ' '))
    pass;                      #log__('old_s, new_s={}',(old_s, new_s)  ,__=(log4fun,_log4mod))
    if not old_s or not new_s or old_s==new_s:
        return app.msg_status(_('Reindent skipped'))
    
    lines   = [ed.get_text_line(row) for row in range(rSelB, rSelE+1)]
    def reind_line(line, ost_l, nst):
        pass;                  #log__('line={}',repr(line)  ,__=(log4fun,_log4mod))
        if not line.startswith(ost_l[0]):    return line
        for n in range(1, 1000):
            if n == len(ost_l):
                ost_l.append(ost_l[0]*n)
            if not line.startswith(ost_l[n]):
                break
        pass;                  #log__('n,len(ost_l[n-1])={}',(n,len(ost_l[n-1]))  ,__=(log4fun,_log4mod))
        new_line    = nst*n + line[len(ost_l[n-1]):]
        pass;                  #log__('new={}',repr(new_line)  ,__=(log4fun,_log4mod))
        return new_line
    ost_l   = [old_s*n for n in range(1,20)]
    lines   = [reind_line(l, ost_l, new_s) for l in lines]
    pass;                      #log__('rSelB, rSelE, lines={}',(rSelB, rSelE, lines)  ,__=(log4fun,_log4mod))
    ed.replace_lines(rSelB, rSelE, lines)
    ed.set_caret(0,rSelE+1, 0,rSelB)
   #def reindent
    

def indent_sel_as_1st():
    crts    = ed.get_carets()
    if len(crts)>1:
        return app.msg_status(_("{} doesn't work with multi-carets").format(_('Command')))
    (cCrt, rCrt
    ,cEnd, rEnd)    = crts[0]
    if rEnd==-1:
        return app.msg_status(_('Need selected lines'))
    (rSelB, cSelB), \
    (rSelE, cSelE)  = apx.minmax((rCrt, cCrt), (rEnd, cEnd))
    rSelE           = rSelE - (1 if 0==cSelE else 0)
    if rSelB==rSelE:
        return app.msg_status(_('Need more than one selected lines'))

    first_s     = ed.get_text_line(rSelB)
    prfx_1st    = re.match(r'\s*', first_s).group(0) if first_s[0] in ' \t' else ''
    lines       = [ed.get_text_line(row)    for row  in range(rSelB+1, rSelE+1)]
    lines       = [prfx_1st+line.lstrip()   for line in lines]
    ed.replace_lines(rSelB+1, rSelE, lines)
   #def indent_sel_as_1st
    

def indent_sel_as_bgn():
    '''
    Aligns multi-line selections.
    Changes all lines in sel except 1st, re-indents lines to make
    indent like in 1st line.
    Indent of 1st line detected by pos of selection start.

    Author: github.com/Alexey-T
    Draft:  github.com/kvichans/cuda_ext/issues/93#issuecomment-372763018
    '''
    if ed.get_sel_mode() != app.SEL_NORMAL:
        return app.msg_status(_('Required normal selection(s)'))

    def _get_indent(s, tabsize):
        r = 0
        for ch in s:
            if ch==' ': r += 1
            elif ch=='\t': r += tabsize
            else: return r
        return r

    carets = ed.get_carets()
    carets_fixed = 0
    for caret in reversed(carets):
        x1, y1, x2, y2 = caret
        if y2<0 or y1==y2: continue

        #sort x,y
        if y1>y2:
            x1, y1, x2, y2 = x2, y2, x1, y1

        lines = ed.get_text_substr(x1, y1, x2, y2).splitlines()
        tabsize = ed.get_prop(app.PROP_TAB_SIZE)
        indent_char = ' ' if ed.get_prop(app.PROP_TAB_SPACES) else '\t'
        indent_need = x1

        for i in range(1, len(lines)):
            s = lines[i]

            while _get_indent(s, tabsize) > indent_need:
                s = s[1:]
            while _get_indent(s, tabsize) < indent_need:
                s = indent_char+s

            lines[i] = s

        ed.replace(x1, y1, x2, y2, '\n'.join(lines))
        carets_fixed += 1

    if carets_fixed>0:
        app.msg_status(
            _('Aligned selection for {} of {} caret(s)').format(
            carets_fixed, len(carets)))
    else:
        app.msg_status(_('Nothing to align'))
   #def indent_sel_as_bgn
    

def align_sel_by_margin(how):
    pass;                      #log__('ok',()  ,__=(log4fun,_log4mod))
    if not apx.get_opt('tab_spaces', False):
        return app.msg_status(_('Fail to use Tab to align'))
    mrgn    = apx.get_opt('margin', 0)
    mrgn    = app.dlg_input(_('Align by margin value:'), str(mrgn))
    if not mrgn or 0==int(mrgn): return 
    mrgn    = int(mrgn)
    pass;                      #log__('mrgn={}',(mrgn)  ,__=(log4fun,_log4mod))
    def align_line(line):
        strpd   = line.strip()
        lstr    = len(strpd)
        if lstr >= mrgn:
            pass;              #log__('lstr >= mrgn',()  ,__=(log4fun,_log4mod))
            return  strpd                               # only strip
        if how=='r':
            return  ' '*(mrgn-lstr) + strpd             # r-align
        return      ' '*           int((mrgn-lstr)/2) \
                   +strpd                             \
                   +' '*(mrgn-lstr-int((mrgn-lstr)/2))  # c-align
       #def align_line
    crts    = ed.get_carets()
    for crt in crts:
        (cCrt, rCrt
        ,cEnd, rEnd)    = crts[0]
        if rEnd==-1:
            cEnd, rEnd  = cCrt, rCrt
        (rSelB, cSelB), \
        (rSelE, cSelE)  = apx.minmax((rCrt, cCrt), (rEnd, cEnd))
        rSelE           = rSelE - (1 if 0==cSelE else 0)
        lines           = [align_line(ed.get_text_line(row))
                            for row in range(rSelB, rSelE+1)]
        ed.replace_lines(rSelB, rSelE, lines)
       #for crt
   #def align_sel_by_margin


def join_lines():
    if app.app_api_version()<'1.0.187': return app.msg_status(_('Need update application'))
    crts    = ed.get_carets()
    if len(crts)>1:
        return app.msg_status(_("{} doesn't work with multi-carets").format(_('Command')))
    (cCrt, rCrt
    ,cEnd, rEnd)    = crts[0]
    (rSelB, cSelB), \
    (rSelE, cSelE)  = apx.minmax((rCrt, cCrt), (rEnd, cEnd))
    rSelE           = rSelE - (1 if 0==cSelE else 0)

    #no selection? do like Sublime: join with next line
    if rEnd==-1 or rEnd==rCrt or rSelB==rSelE:
        y = rCrt
        if y >= ed.get_line_count()-1: return #last line
        s1 = ed.get_text_line(y)
        x = len(s1)
        s2 = ed.get_text_line(y+1)
        if s2: #add space only for non-blank line
            s1 += ' '+s2
            x += 1
        ed.replace_lines(y, y+1, [s1])
        ed.set_caret(x, y)
        return    

    first_ln= ed.get_text_line(rSelB)
    last_ln = ed.get_text_line(rSelE)
    lines   = [first_ln.rstrip()] \
            + [ed.get_text_line(row).strip() for row in range(rSelB+1, rSelE)] \
            + [last_ln.lstrip()]
    joined  = ' '.join(l for l in lines if l)
    _replace_lines(ed, rSelB, rSelE, joined)
    ed.set_caret(0,rSelB+1, 0,rSelB)
   #def join_lines
    

def del_more_spaces():
    if app.app_api_version()<'1.0.187': return app.msg_status(_('Need update application'))
    crts    = ed.get_carets()
    if len(crts)>1:
        return app.msg_status(_("{} doesn't work with multi-carets").format(_('Command')))
    (cCrt, rCrt
    ,cEnd, rEnd)    = crts[0]
    sel     = ed.get_text_sel()
    if not sel:
        body    = ed.get_text_all()
        new_body= re.sub('  +', ' ', body)
        if body==new_body:
            return app.msg_status(_('No duplicate spaces'))
        ed.set_text_all(new_body)
        ed.set_caret(cCrt, rCrt)
        return app.msg_status(f(_('Deleted spaces: {}'), len(body)-len(new_body)))
    new_sel = re.sub('  +', ' ', sel)
    if sel==new_sel:
        return app.msg_status(_('No duplicate spaces'))
    (rSelB, cSelB), \
    (rSelE, cSelE)  = apx.minmax((rCrt, cCrt), (rEnd, cEnd))
    cCrt, rCrt      = ed.replace(cSelB, rSelB, cSelE, rSelE, new_sel)
    ed.set_caret(cCrt, rCrt, cSelB, rSelB)
    return app.msg_status(f(_('Deleted spaces: {}'), len(sel)-len(new_sel)))
   #def del_more_spaces
    

def _rewrap(margin, cmt_sgn, save_bl, rTx1, rTx2, sel_after):
    
    tab_sz  = apx.get_opt('tab_size', 8)
    lines   = [ed.get_text_line(nln) for nln in range(rTx1, rTx2+1)]
    pass;                      #log__('lines={}',(lines)  ,__=(log4fun,_log4mod))
    # Extract prefix by comment-sign
    cm_prfx = ''
    if lines[0].lstrip().startswith(cmt_sgn):
        # First line commented - need for all
        cm_prfx = lines[0][:lines[0].index(cmt_sgn)+len(cmt_sgn)]
        if not all(map(lambda l:l.startswith(cm_prfx), lines)):
            return app.msg_status('Re-wrap needs same positions of comments')
    pass;                      #log__('1 cm_prfx={}',repr(cm_prfx)  ,__=(log4fun,_log4mod))
    # Can prefix is wider?
    if save_bl:
        for ext in range(1,100):
            if False:pass
            elif all(map(lambda l:l.startswith(cm_prfx+' '),  lines)):
                cm_prfx += ' '
            elif all(map(lambda l:l.startswith(cm_prfx+'\t'), lines)):
                cm_prfx += '\t'
            else:
                break#for ext
           #for ext
    pass;                      #log__('2 cm_prfx={}',repr(cm_prfx)  ,__=(log4fun,_log4mod))
    if len(cm_prfx)+10>margin:
        return app.msg_status('No text to re-wrap')
    # Join
    lines   = [line[len(cm_prfx):] for line in lines]
    if not save_bl:
        lines   = [line.lstrip() for line in lines]
    text    = ' '.join(lines)
    pass;                      #log__('mid text={}',('\n'+text)  ,__=(log4fun,_log4mod))
    # Split by margin
    margin -= (len(cm_prfx) + (tab_sz-1)*cm_prfx.count('\t'))
    pass;                      #log__('margin,tab_sz={}',(margin,tab_sz)  ,__=(log4fun,_log4mod))
    words   = [(m.start(), m.end(), m.group())
                for m in re.finditer(r'\b\S+\b', text)]
    pass;                      #log__('words={}',(words)  ,__=(log4fun,_log4mod))
    lines   = []
    last_pos= 0
    for word in words:
        pass;              #LOG and log('last_pos, word[1]-last_pos, word={}',(last_pos, word[1]-last_pos, word))
        if word[1] - last_pos >= margin:
            line    = text[last_pos:word[0]]
            if line[-1] == ' ':
                line    = line[:-1]
            lines  += [line]
            last_pos= word[0]
    lines  += [text[last_pos:]]
    # Re-join
    text    = '\n'.join(cm_prfx+line for line in lines)
    pass;                      #log__('fin text={}',('\n'+text)  ,__=(log4fun,_log4mod))
    # Modify ed
    _replace_lines(ed, rTx1, rTx2, text)
    if sel_after:
        ed.set_caret(0,rTx1+len(lines), 0,rTx1)
   #def _rewrap


def rewrap_cmt_at_caret():
    if app.app_api_version()<'1.0.187': return app.msg_status(_('Need update application'))
    margin  = apx.get_opt('margin', 0)
    lex     = ed.get_prop(app.PROP_LEXER_FILE, '')
    if not lex: return app.msg_status(_('Need lexer active'))
    cmt_sgn = app.lexer_proc(app.LEXER_GET_PROP, lex)['c_line']     if lex else ''
    if not cmt_sgn: return app.msg_status(_('Need lexer with line-comment chars'))
        
    x, y, x1, y1 = ed.get_carets()[0]
    line = ed.get_text_line(y)
    if not line.lstrip().startswith(cmt_sgn):
        return app.msg_status(_('Current line is not line-comment'))
    prefix = line[:line.find(cmt_sgn)+len(cmt_sgn)]
    line1 = y
    line2 = y
    while line1>0 and ed.get_text_line(line1-1).startswith(prefix):
        line1 -= 1
    while line2<ed.get_line_count()-1 and ed.get_text_line(line2+1).startswith(prefix):
        line2 += 1
        
    _rewrap(margin, cmt_sgn, True, line1, line2, False)
   #def rewrap_cmt_at_caret


def rewrap_sel_by_margin():
    if len(ed.get_carets())>1:          return app.msg_status(_("Command doesn't work with multi-carets"))
    if app.app_api_version()<'1.0.187': return app.msg_status(_('Need update application'))
    margin  = apx.get_opt('margin', 0)
    lex     = ed.get_prop(app.PROP_LEXER_FILE, '')
    cmt_sgn = app.lexer_proc(app.LEXER_GET_PROP, lex)['c_line']     if lex else ''

    ag  = DlgAg(form=d(cap=_('Re-wrap lines')       ,w=5+165+5, h=5+120+5)
               ,ctrls=[0
        ,('mar_',d(tp='labl',tid='marg' ,x=5        ,w=110  ,cap=_('&Margin:')      )) # &m
        ,('marg',d(tp='edit',y=5        ,x=5+105    ,w=60                           )) # 
        ,('csg_',d(tp='labl',tid='csgn' ,x=5        ,w=110  ,cap=_('&Comment sign:'))) # &c
        ,('csgn',d(tp='edit',y=5+30     ,x=5+105    ,w=60                           ))
        ,('svbl',d(tp='chck',y=5+60     ,x=5        ,w=165  ,cap=_('&Keep indent')  )) # &s
        ,('okok',d(tp='bttn',y=5+120-28 ,x=5        ,w=80   ,cap=_('OK'), def_bt='1',on=CB_HIDE)) #
        ,('cncl',d(tp='bttn',y=5+120-28 ,x=5+80+5   ,w=80   ,cap=_('Cancel')        ,on=CB_HIDE))
               ][1:]
               ,vals=d(marg=str(margin)
                      ,csgn=cmt_sgn
                      ,svbl=True)
               ,fid='marg'
        )
    aid,vals    = ag.show()
    if aid!='okok': return 

    if not vals['marg'].isdigit(): return app.msg_status(_('Not digit margin'))
    margin  = int(vals['marg'])
    cmt_sgn =     vals['csgn']
    save_bl =     vals['svbl']
        
    crts    = ed.get_carets()
    cCrt, rCrt, \
    cEnd, rEnd  = crts[0]
    cEnd, rEnd  = (cCrt, rCrt) if -1==rEnd else (cEnd, rEnd)
    (rTx1,cTx1),\
    (rTx2,cTx2) = apx.minmax((rCrt, cCrt), (rEnd, cEnd))
    rTx2        = rTx2-1 if cTx2==0 and rTx1!=rTx2 else rTx2
    pass;                      #log__('rTx1, rTx2={}',(rTx1, rTx2)  ,__=(log4fun,_log4mod))

    def find_paragraphs_in_range(line1, line2):
        " Author: github.com/Alexey-T "
        rng = []
        n2 = line2
        while True:
            if n2<line1: break 
            while (n2>=line1) and not ed.get_text_line(n2).strip():
                n2 -= 1
            if n2<line1: break
        
            n1 = n2 
            while (n1>line1) and ed.get_text_line(n1-1).strip():
                n1 -= 1
        
            rng.insert(0, (n1, n2))
            n2 = n1-1
        return rng
       #def find_paragraphs_in_range
        
    # Must processs lines by paragraphs to keep blank-only lines
    ranges = find_paragraphs_in_range(rTx1, rTx2)
    for rng in reversed(ranges):
        _rewrap(margin, cmt_sgn, save_bl, rng[0], rng[1], True)
#   _rewrap(    margin, cmt_sgn, save_bl, rTx1, rTx2, True)
   #def rewrap_sel_by_margin
        

def align_sel_by_sep():
    pass;                      #log("ok")
    strs = []
    lens = []
    col_cnt = 0
    
    SEP = app.dlg_input(_('Separator char:'), ',')
    if SEP is None: return
    if len(SEP) != 1:
        return app.msg_status(_('Wrong separator char')) 

    def split_seps(s, sep):
        res = []        
        quote = False
        item = ''
        i = -1
    
        while True:
            i += 1
            if i>=len(s):
                break
            ch = s[i]
            if not quote and ch==sep:
                res.append(item.rstrip(' '))
                item = ''
                continue
            item += ch
            if quote and ch=='\\':
                i += 1
                if i<len(s):
                    item += s[i]
                continue
            if ch in '\'"':
                quote = not quote
                continue
        res.append(item.strip(' '))
        return res
                
    lns = ed.get_sel_lines()
    if lns[0]<0:
        return app.msg_status(_('No selection'))
        
    text = ed.get_text_sel()
    if not text:
        return app.msg_status(_('No selection'))
        
    for s in text.split('\n'):
        if s.strip(' '):
            r = split_seps(s, SEP)
            strs.append(r)
            lens.append([len(i) for i in r])
            col_cnt = max(col_cnt, len(r))
                
    cols = []
    for i in range(col_cnt):
        col = 0
        for l in lens:
            if i<len(l):
                col = max(col, l[i])
        cols.append(col)
                    
    pass;                      #log(cols)
    def ch(r):
        return SEP.join([s.ljust(cols[i]) for (i, s) in enumerate(r)])
            
    res = [ch(r) for r in strs]
    pass;                      #log('\n'.join(res))
    ed.replace_lines(lns[0], lns[1], res)
    app.msg_status(f(_('Replaced {} line(s)'), len(strs)))
   #def align_sel_by_sep
        

def align_by_carets():
    # Ludger Ostrop-Lutterbeck, 2021
    
    crts = ed.get_carets()
    if len(crts) <= 1:
        return app.msg_status(_('Command does only work with multi-carets'))
        
    for (x, y, x1, y1) in crts:
        if y1 >= 0:
            return app.msg_status(_('This command cannot handle selection(s)'))    
    
    # Determine carets to be ignored with mulitple carets in one line 
    # To_be_discussed: 
    #   One posibility is to align at the rightmost carets position of multiple carets in a line.
    #   The alternative is to do it the other way round and take the leftmost as the relevant one 
    #       and ignore the carets further right.
    #   I'm really not sure about what's being the better aproach. 
    crts_to_ignore = []
    
    # Take rightmost caret and ignore all carets to the left in the same line 
    for i in range(len(crts) - 1):
        if crts[i][1] == crts[i + 1][1]:
            crts_to_ignore.append(crts[i])
 
    # As an alternative take the leftmost caret and ignore all carets to the right in the same line
#   for i in reversed(range(len(crts))):
#       if ((i - 1) >=0) and (crts[i][1] == crts[i - 1][1]):
#           crts_to_ignore.append(crts[i])
 
    crts_relevant = list(set(crts).difference(set(crts_to_ignore)))

    # Get position of rightmost caret
    max_pos_x = max(crts_relevant, key=itemgetter(0))[0]
        
    # Delete all carets 
    ed.set_caret(-1, -1, -1, -1, id=app.CARET_DELETE_ALL, options=0)
     
    # Align content by carets at  position of rightmost caret, replace lines and restore rightmost carets of each line  
    for (x, y, x1, y1) in crts_relevant:
        len_line = len(ed.get_text_line(y))
        
        spaces = ' ' * (max_pos_x - x)
        nline = ed.get_text_substr(0, y, x, y) + spaces + ed.get_text_substr(x, y, len_line, y) 
        ed.replace(0, y, len_line, y, nline)
        
        ed.set_caret(x + len(spaces), y, -1, -1, id=app.CARET_ADD, options=0) 
        # To_be_discussed: 
        #   as an alternative the carets could be set not a the position of the alignment but at their former position
        #   I prefer the solution above with carets being at the position of the alignment    
#       ed.set_caret(x, y, -1, -1, id=app.CARET_ADD, options=0)
   #align_by_carets

def _replace_lines(_ed, r_bgn, r_end, newlines):
    """ Replace full lines in [r_bgn, r_end] to newlines """
    if app.app_api_version()<'1.0.187': return app.msg_status(_('Need update application'))
    lines_n     = _ed.get_line_count()
    pass;                      #log__('lines_n, r_bgn, r_end, newlines={}',(lines_n, r_bgn, r_end, newlines)  ,__=(log4fun,_log4mod))
    if r_end < lines_n-1:
        # Replace middle lines
        pass;                  #log__('middle',()  ,__=(log4fun,_log4mod))
        _ed.delete(0,r_bgn, 0,1+r_end)
        _ed.insert(0,r_bgn, newlines+'\n')
    else:
        # Replace final lines
        pass;                  #log__('final',()  ,__=(log4fun,_log4mod))
        _ed.delete(0,r_bgn, 0,lines_n)
        _ed.insert(0,r_bgn, newlines)
   #def _replace_lines

MAX_HIST= apx.get_opt('ui_max_history_edits', 20)
def add_to_hist(val, lst):
    """ Add/Move val to list head. """
    if val in lst:
        if 0 == lst.index(val):   return lst
        lst.remove(val)
    lst.insert(0, val)
    if len(lst)>MAX_HIST:
        del lst[MAX_HIST:]
    return lst
   #def add_to_hist

