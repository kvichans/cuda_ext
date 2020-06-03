''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '1.7.15 2020-06-03'
ToDo: (see end of file)
'''

import  re, os, sys

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

d       = dict
C1      = chr(1)

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
        M,m     = self.__class__,self
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
                         ,h=35, h_max=35                        # Only horz resize
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
            if tag=='help':             return (app.msg_box(FiL.HELP_C, app.MB_OK)  , [])[1]
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
    ),d(tag='nmdl'  ,cap=_('Work in non-modal mod&e (close dialog)'),ch=FiL.opts['nmdl'],en=FiL.opts['dock']==''
#   ),d(tag='nmdl'  ,cap=_('Do not hide on &ESC (close dialog)')    ,ch=FiL.opts['nmdl'],en=FiL.opts['dock']==''
    ),d(tag='dckt.' ,cap=_('Dock to window &top (close dialog)')    ,ch=FiL.opts['dock']=='t'
    ),d(tag='dckb.' ,cap=_('Dock to window &bottom (close dialog)') ,ch=FiL.opts['dock']=='b'
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
    ((rTx1, cTx1)
    ,(rTx2, cTx2))  = apx.minmax((rCrt, cCrt), (rEnd, cEnd))
    ls_txt  = ed.get_text_substr(0,rTx1, 0,rTx2+(0 if 0==cEnd else 1))
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
    ed.delete(0,rTx1, 0,rTx2+(0 if 0==cEnd else 1))
    ed.insert(0,rTx1, '\n'.join(nlines)+'\n')
    ed.set_caret(0,rTx1+len(nlines), 0, rTx1)
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
            app.msg_box(_('Fill "Old step".\n\n')+fill_h, app.MB_OK)
            return d(fid='olds')
        if ''==vals['news'] or vals['news'][0] not in ' .t2345678':
            app.msg_box(_('Fill "New step".\n\n')+fill_h, app.MB_OK)
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
    if rEnd==-1 or rEnd==rCrt or rSelB==rSelE:
        return app.msg_status(_("{} works with multiline selection").format(_('Command')))
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

    ag  = DlgAg(form=d(cap=_('Re-wrap lines'), w=5+165+5, h=5+120+5)
               ,ctrls=[0
        ,('mar_',d(tp='labl',tid='marg' ,x=5        ,w=120  ,cap=_('&Margin:')      )) # &m
        ,('marg',d(tp='edit',y=5        ,x=5+120    ,w=45                           )) # 
        ,('csg_',d(tp='labl',tid='csgn' ,x=5        ,w=120  ,cap=_('&Comment sign:'))) # &c
        ,('csgn',d(tp='edit',y=5+30     ,x=5+120    ,w=45                           ))
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

    if not vals['marg'].isdigit(): return app.msg_status('Not digit margin')
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

