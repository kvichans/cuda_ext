''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '1.7.01 2019-03-28'
ToDo: (see end of file)
'''

import  re, os, sys

import  cudatext            as app
from    cudatext        import ed
from    cudatext_keys   import *
import  cudatext_cmd        as cmds
import  cudax_lib           as apx
from    cuda_kv_base    import *
from    cuda_kv_dlg     import *

try:# I18N
    _   = get_translation(__file__)
except:
    _   = lambda p:p

pass;                           _log4mod = LOG_FREE  # Order log in the module

d       = dict
c1      = chr(1)

fil_restart_dlg= False
fil_ed_crts    = None                      # Carets at start
fil_what       = None                      # String to search 

def dlg_find_in_lines(): #NOTE: dlg_find_in_lines
    global fil_restart_dlg, fil_ed_crts, fil_what
    fil_ed_crts= ed.get_carets()          # Carets at start
    fil_what   = None
    while True:
        fil_restart_dlg  = False
        _dlg_FIL()
        if not fil_restart_dlg:  break

def _dlg_FIL():
    pass;                       log4fun=-1== 1  # Order log in the function
#   FORM_C  = f(_('Find in Lines {}'), 1+ed.get_prop(app.PROP_INDEX_GROUP))
    FORM_C  =   _('Find in Lines')
    HELP_C  = _(
        '• Search "in Lines" starts on Enter or Shift+Enter or immediately (if "Instant search" is tuned on).'
      '\r• A found fragment after first caret will be selected.'
      '\r• All found fragments are remembered and dialog can jump over them by [Shift+]Enter or by menu commands.'
      '\r• Option ".*" (regular expression) allows to use Python reg.ex. See "docs.python.org/3/library/re.html".'
      '\r• Option "w" (whole words) is ignored if entered string contains not a word.'
#     '\r• If option "Close on success" (in menu) is tuned on, dialog will close after successful search.'
      '\r• If option "Instant search" (in menu) is tuned on, search result will be updated on start and after each change of pattern.'
      '\r• Command "Restore initial selection" (in menu) restores only first of initial carets.'
      '\r• Ctrl+F (or Ctrl+R) to call appication dialog Find (or Replace).'
    )
    pass;                      #log('###',()) if iflog(log4fun,_log4mod) else 0
    pass;                      #log('hist={}',(get_hist('find.find_in_lines'))) if iflog(log4fun,_log4mod) else 0
    opts    = d(reex=False,case=False,word=False,hist=[]           ,usel=False,inst=False,insm=3)
#   opts    = d(reex=False,case=False,word=False,hist=[],clos=False,usel=False,inst=False)
    opts.update(get_hist('find.find_in_lines', opts))

    # How to select node
    select_frag = lambda frag_inf:  ed.set_caret(*frag_inf)
        
    # Ask
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
    compile_pttn= lambda    pttn_s, reex, case, word: re.compile(
                            pttn_s          if reex else
                      r'\b'+pttn_s+r'\b'    if word and re.match('^\w+$', pttn_s) else
                  re.escape(pttn_s)
                        ,   0 if case else re.I)
        
    prev_wt = None          # Prev what
    ready_l = []            # [(row,col_bgn,col_end)]
    ready_p = -1            # pos in ready_l
    form_cap= lambda: f('{} ({}/{})', FORM_C, 1+ready_p, len(ready_l)) if ready_l else f('{} (0)', FORM_C)
    form_cpw= lambda: FORM_C + (f(_(' (Type {} character(s) to find)'), opts['insm'])
                                    if opts['inst'] else
                                  _(' (ENTER to find)'))
    form_err= lambda: FORM_C +  _(' (Error)')
        
    def switch_to_dlg(ag, dlg='find'):
        ag.opts['on_exit_focus_to_ed'] = None
        ag.hide()
        ed.cmd(cmds.cmd_DialogFind if dlg=='find' else cmds.cmd_DialogReplace)
        if app.app_api_version()>='1.0.248':
            app.app_proc(app.PROC_SET_FINDER_PROP, d(
                find_d      = ag.val('what')
            ,   op_regex_d  = ag.val('reex')
            ,   op_case_d   = ag.val('case')
            ,   op_word_d   = ag.val('word')
            ))
    def do_attr(ag, aid, data=''):
        nonlocal prev_wt
        prev_wt = ''
        return do_find(ag, 'find', 'stay')  # if opts['inst'] else d(fid='what')
    def do_menu(ag, aid, data=''):
        def wnen_menu(ag, tag):
            nonlocal opts
            if tag in ('clos','usel','inst'):   opts[tag] = not opts[tag]
            if tag=='help':                     app.msg_box(HELP_C, app.MB_OK)
            if tag in ('prev','next'):          return do_find(ag, tag)
            if tag=='rest':
                ed.set_caret(*fil_ed_crts[0])
                return None
            if tag=='insm':
                insm    = app.dlg_input(_('Instant search minimum'), str(opts['insm']))
                opts['insm']    = int(insm) if insm and re.match(r'^\d+$', insm) else opts['insm']
            if tag=='inst':
                fil_what         = ag.val('what')
                fil_restart_dlg  = True
                return None
            if tag=='natf':
                switch_to_dlg(ag)
                return None
            return []
           #def wnen_menu
        insm_c  = f(_('Instant search minimum: {}...'), opts['insm'])
        ag.show_menu(set_all_for_tree(
            [ d(    tag='help'  ,cap=_('&Help...')                                      
            ),d(                 cap='-'
            ),d(    tag='prev'  ,cap=_('Find &previous')                                ,key='Shift+Enter'
            ),d(    tag='next'  ,cap=_('F&ind next')                                    ,key='Enter'
            ),d(                 cap='-'
            ),d(                 cap=_('&Options')  ,sub=
                [ d(tag='usel'  ,cap=_('Use selection from text')   ,ch=opts['usel']    
                ),d(tag='inst'  ,cap=_('Instant search')            ,ch=opts['inst']    
                ),d(tag='insm'  ,cap=insm_c                                             
            )]),d(               cap='-'
            ),d(    tag='natf'  ,cap=_('Call native Find dialog')                       ,key='Ctrl+F'
            ),d(    tag='rest'  ,cap=_('Restore initial selection and close dialog &=') ,key='Shift+Esc'
            )], 'sub', 'cmd', wnen_menu)    # Set cmd=wnen_menu for all nodes
        ,   aid
        )
        return d(fid='what')
       #def do_menu
    def do_find(ag, aid, data=''):
        nonlocal opts, prev_wt, ready_l, ready_p
        pass;                  #log('aid, data={}',(aid, data)) if iflog(log4fun,_log4mod) else 0
        # What/how will search
        prnx    = 'prev' if aid=='prev' else 'next'
        crt     = ed.get_carets()[0][:]     # Current first caret (col,row, col?,row?)
        min_rc  = (crt[1], crt[0])  if crt[2]==-1 else  min((crt[1], crt[0]), (crt[3], crt[2]))
        max_rc  = (crt[1], crt[0])  if crt[2]==-1 else  max((crt[1], crt[0]), (crt[3], crt[2]))
        what    = ag.val('what')
        if prev_wt==what and ready_l:# and 'stay' not in data:
            pass;              #log('will jump',()) if iflog(log4fun,_log4mod) else 0
            if 1==len(ready_l):                         return  d(fid='what')
            ready_p = (ready_p + (-1 if aid=='prev' else 1)) % len(ready_l)
            select_frag(ready_l[ready_p])
            return                      d(form=d(cap=form_cap()) ,fid='what')
        prev_wt  = what
        if not what:
            ready_l, ready_p    = [], -1
            return                      d(form=d(cap=form_cpw()) ,fid='what')
        if opts['inst'] and len(what)<opts['insm'] and not opts['reex'] :
            ready_l, ready_p    = [], -1
            return                      d(form=d(cap=form_cpw()) ,fid='what')
        if not opts['inst']:
            opts['hist']= add_to_hist(what, opts['hist'])
        opts.update(ag.vals(['reex','case','word']))
        # New search
        ready_l = []
        ready_p = -1
        pttn_r  = None
        try:
            pttn_r  = compile_pttn(what, opts['reex'], opts['case'], opts['word'])
        except:
            return d(ctrls=[('what',d(items=opts['hist']))]
                    ,form=d(cap=form_err())
                    ,fid='what')
        for row in range(ed.get_line_count()):
            line    = ed.get_text_line(row)
            mtchs   = pttn_r.finditer(line)
            if not mtchs:  continue
            for mtch in mtchs:
                fnd_bgn = mtch.start()
                fnd_end = mtch.end()
#               if opts['clos']:
#                   select_frag(fnd_end, row, fnd_bgn, row)
#                   return None         # Close dlg
                ready_p = (len(ready_l)
                            if prnx=='next' and ready_p==-1 and                             # Need next and no yet
                                (row>max_rc[0] or row==max_rc[0] and fnd_bgn>max_rc[1])     # At more row or at more col in cur row
                            or prnx=='prev'                 and                             # Need prev
                                (row<min_rc[0] or row==min_rc[0] and fnd_end<min_rc[1])     # At less row or at less col in cur row
                            else ready_p)
                ready_l+= [(fnd_end, row, fnd_bgn, row)]
        pass;                  #log('ready_l={}',(ready_l)) if iflog(log4fun,_log4mod) else 0
        ready_p = max(0, ready_p) if ready_l else -1
        pass;                  #log('ready_p={}',(ready_p)) if iflog(log4fun,_log4mod) else 0
        # Show results
        if ready_l:
            if aid=='find' and 'stay' in data:
                ready_p = (ready_p-1) % len(ready_l)
            pass;              #log('show rslt ready_p={}',(ready_p,)) if iflog(log4fun,_log4mod) else 0
            select_frag(ready_l[ready_p])
        return d(ctrls=[('what',d(items=opts['hist']))]
                ,form=d(cap=form_cap())
                ,fid='what')
       #def do_find
    what    = fil_what              if fil_what is not None      else \
              ed.get_text_sel()     if opts['usel'] and 1==len(ed.get_carets()) else ''
    what    = '' if '\r' in what or '\n' in what else what
#   ag      = None
    def do_key_down(ag, key, data=''):
        scam    = data if data else app.app_proc(app.PROC_GET_KEYSTATE, '')
        if 0:pass
        elif (scam,key)==('s',VK_ENTER):        # Shift+Enter
            ag.update(do_find(ag, 'prev'))
        elif (scam,key)==('s',VK_ESCAPE):       # Shift+Esc
            ed.set_caret(*fil_ed_crts[0])
            ag.hide()
        elif (scam,key)==('c',ord('F')) or (scam,key)==('c',ord('R')):        # Ctrl+F or Ctrl+R
            switch_to_dlg(ag, 'find' if key==ord('F') else 'repl')
        else: return [] # Nothing
        return False    # Stop event
    wh_tp   = 'edit'    if opts['inst'] else 'cmbx'
    wh_call = do_find   if opts['inst'] else None
    ag      = DlgAg(
        form    =dict(cap=form_cpw(), w=255, h=35, h_max=35
                     ,on_key_down=do_key_down
#                    ,border=app.DBORDER_SIZE
                     ,border=app.DBORDER_TOOLSIZE
#                    ,resize=True
                     )
    ,   ctrls   =[0
  ,('find',d(tp='bttn'  ,y=0        ,x=-99      ,w=44   ,cap=''     ,sto=False  ,def_bt='1'         ,on=do_find         ))  # Enter
  ,('reex',d(tp='chbt'  ,tid='what' ,x=5+38*0   ,w=39   ,cap='.&*'  ,hint=_('Regular expression')   ,on=do_attr         ))  # &*
  ,('case',d(tp='chbt'  ,tid='what' ,x=5+38*1   ,w=39   ,cap='&aA'  ,hint=_('Case sensitive')       ,on=do_attr         ))  # &a
  ,('word',d(tp='chbt'  ,tid='what' ,x=5+38*2   ,w=39   ,cap='"&w"' ,hint=_('Whole words')          ,on=do_attr         ))  # &w
  ,('what',d(tp=wh_tp   ,y  =5      ,x=5+38*3+5 ,w=85   ,items=opts['hist']                         ,on=wh_call ,a='r>' ))  # 
  ,('menu',d(tp='bttn'  ,tid='what' ,x=210      ,w=40   ,cap='&='                   ,on_menu=do_menu,on=do_menu ,a='>>' ))  # &=
                ][1:]
    ,   fid     ='what'
    ,   vals    = upd_dict({k:opts[k] for k in ('reex','case','word')}, d(what=what))
                          #,options={'gen_repro_to_file':'repro_dlg_find_in_lines.py'}
    )
    if opts['inst'] and what:
        ag.update(do_find(ag, 'find', 'stay'))
    ag.show(lambda ag: set_hist('find.find_in_lines', upd_dict(opts, ag.vals(['reex','case','word']))))
   #def _dlg_FIL


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

    ed.cmd(cmds.cmd_FinderAction, c1.join([]
        +['findprev' if updn=='up' else 'findnext']
        +[clip]
        +['']
        +[find_opt]
    ))
    if app.app_api_version()>='1.0.248':
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
    pass;                      #log('seltext,clip,find_opt={!r}',(seltext,clip,find_opt)) if iflog(log4fun,_log4mod) else 0
    ed.cmd(cmds.cmd_FinderAction, c1.join([]
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
    crts    = ed.get_carets()
    if len(crts)>1:
        return app.msg_status(_("{} doesn't work with multi-carets").format(_('Command')))
    (cCrt, rCrt
    ,cEnd, rEnd)    = crts[0]
    if rEnd==-1 or rEnd==rCrt:
        return app.msg_status(_("{} works with multiline selection").format(_('Command')))
    spr     = app.dlg_input('Enter separator string', data4_align_in_lines_by_sep)
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
    fill_h      = _('To specify two/four/eight blanks enter'
                    '\r    these blanks'
                    '\ror'
                    '\r    "2b"/"4b"/"8b"'
                    '\ror'
                    '\r    ".."/"...."/"........" (dots).'
                    '\rTo specify TAB enter "t".'
                  )
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
            app.msg_box(_('Fill "Old step".\n\n'+fill_h.replace('\r', '\n')), app.MB_OK)
            return d(fid='olds')
        if ''==vals['news'] or vals['news'][0] not in ' .t2345678':
            app.msg_box(_('Fill "New step".\n\n'+fill_h.replace('\r', '\n')), app.MB_OK)
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
    ,('cncl',d(tp='bttn',y=90       ,x=245-80-5 ,w= 80  ,cap=_('Cancel')                            ))
            ][1:]
        ,   vals    = vals
        ,   fid     = 'olds'
        )
    aid, vals   = ag.show()
    if not aid: return 
    old_s   = parse_step(vals['olds'].replace('.', ' '))
    new_s   = parse_step(vals['news'].replace('.', ' '))
    pass;                      #log('old_s, new_s={}',(old_s, new_s)) if iflog(log4fun,_log4mod) else 0
    if not old_s or not new_s or old_s==new_s:
        return app.msg_status(_('Reindent skipped'))
    
#   fid         = 'olds'
#   while True:
#       btn,vals,_t,_p = dlg_wrapper(f(_('Reindent selected lines ({})'), rSelE-rSelB+1), 245,120,     #NOTE: dlg-reindent
#            [dict(           tp='lb'   ,tid='olds' ,l=5        ,w=150  ,cap='>'+_('&Old indent step:') ,hint=fill_h) # &o
#            ,dict(cid='olds',tp='ed'   ,t=10       ,l=5+150+5  ,w= 80                                              ) # 
#            ,dict(           tp='lb'   ,tid='news' ,l=5        ,w=150  ,cap='>'+_('&New indent step:') ,hint=fill_h) # &n
#            ,dict(cid='news',tp='ed'   ,t=50       ,l=5+150+5  ,w= 80                                              )
#            ,dict(cid='!'   ,tp='bt'   ,t=90       ,l=245-170-5,w= 80  ,cap=_('OK')                    ,def_bt='1' ) #   
#            ,dict(cid='-'   ,tp='bt'   ,t=90       ,l=245-80-5 ,w= 80  ,cap=_('Cancel')                            )
#            ],    vals, focus_cid=fid)
#       if btn is None or btn=='-': return None
#       if ''==vals['olds'] or vals['olds'][0] not in ' .t2345678':
#           app.msg_box(_('Fill "Old step".\n\n'+fill_h.replace('\r', '\n')), app.MB_OK)
#           fid = 'olds'
#           continue
#       if ''==vals['news'] or vals['news'][0] not in ' .t2345678':
#           app.msg_box(_('Fill "New step".\n\n'+fill_h.replace('\r', '\n')), app.MB_OK)
#           fid = 'news'
#           continue
#       old_s   = parse_step(vals['olds'].replace('.', ' '))
#       new_s   = parse_step(vals['news'].replace('.', ' '))
#       pass;                  #log('old_s, new_s={}',(old_s, new_s)) if iflog(log4fun,_log4mod) else 0
#       if not old_s or not new_s or old_s==new_s:
#           return app.msg_status(_('Reindent skipped'))
#       break
#      #while
        
    lines   = [ed.get_text_line(row) for row in range(rSelB, rSelE+1)]
    def reind_line(line, ost_l, nst):
        pass;                  #log('line={}',repr(line)) if iflog(log4fun,_log4mod) else 0
        if not line.startswith(ost_l[0]):    return line
        for n in range(1, 1000):
            if n == len(ost_l):
                ost_l.append(ost_l[0]*n)
            if not line.startswith(ost_l[n]):
                break
        pass;                  #log('n,len(ost_l[n-1])={}',(n,len(ost_l[n-1]))) if iflog(log4fun,_log4mod) else 0
        new_line    = nst*n + line[len(ost_l[n-1]):]
        pass;                  #log('new={}',repr(new_line)) if iflog(log4fun,_log4mod) else 0
        return new_line
    ost_l   = [old_s*n for n in range(1,20)]
    lines   = [reind_line(l, ost_l, new_s) for l in lines]
    pass;                      #log('rSelB, rSelE, lines={}',(rSelB, rSelE, lines)) if iflog(log4fun,_log4mod) else 0
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
        return app.msg_status(_('Need more then one selected lines'))

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
    pass;                      #log('ok',()) if iflog(log4fun,_log4mod) else 0
    if not apx.get_opt('tab_spaces', False):
        return app.msg_status(_('Fail to use Tab to align'))
    mrgn    = apx.get_opt('margin', 0)
    pass;                      #log('mrgn={}',(mrgn)) if iflog(log4fun,_log4mod) else 0
    def align_line(line):
        strpd   = line.strip()
        lstr    = len(strpd)
        if lstr >= mrgn:
            pass;              #log('lstr >= mrgn',()) if iflog(log4fun,_log4mod) else 0
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
    pass;                      #log('lines={}',(lines)) if iflog(log4fun,_log4mod) else 0
    # Extract prefix by comment-sign
    cm_prfx = ''
    if lines[0].lstrip().startswith(cmt_sgn):
        # First line commented - need for all
        cm_prfx = lines[0][:lines[0].index(cmt_sgn)+len(cmt_sgn)]
        if not all(map(lambda l:l.startswith(cm_prfx), lines)):
            return app.msg_status('Re-wrap needs same positions of comments')
    pass;                      #log('1 cm_prfx={}',repr(cm_prfx)) if iflog(log4fun,_log4mod) else 0
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
    pass;                      #log('2 cm_prfx={}',repr(cm_prfx)) if iflog(log4fun,_log4mod) else 0
    if len(cm_prfx)+10>margin:
        return app.msg_status('No text to re-wrap')
    # Join
    lines   = [line[len(cm_prfx):] for line in lines]
    if not save_bl:
        lines   = [line.lstrip() for line in lines]
    text    = ' '.join(lines)
    pass;                      #log('mid text={}',('\n'+text)) if iflog(log4fun,_log4mod) else 0
    # Split by margin
    margin -= (len(cm_prfx) + (tab_sz-1)*cm_prfx.count('\t'))
    pass;                      #log('margin,tab_sz={}',(margin,tab_sz)) if iflog(log4fun,_log4mod) else 0
    words   = [(m.start(), m.end(), m.group())
                for m in re.finditer(r'\b\S+\b', text)]
    pass;                      #log('words={}',(words)) if iflog(log4fun,_log4mod) else 0
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
    pass;                      #log('fin text={}',('\n'+text)) if iflog(log4fun,_log4mod) else 0
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
    if aid is None or aid=='cncl': return None

#   aid,vals,_t,chds   = dlg_wrapper(_('Re-wrap lines'), 5+165+5,5+120+5,     #NOTE: dlg-rewrap
#        [dict(           tp='lb'   ,tid='marg' ,l=5        ,w=120  ,cap=_('&Margin:')      ) # &m
#        ,dict(cid='marg',tp='ed'   ,t=5        ,l=5+120    ,w=45                           ) # 
#        ,dict(           tp='lb'   ,tid='csgn' ,l=5        ,w=120  ,cap=_('&Comment sign:')) # &c
#        ,dict(cid='csgn',tp='ed'   ,t=5+30     ,l=5+120    ,w=45                           )
#        ,dict(cid='svbl',tp='ch'   ,t=5+60     ,l=5        ,w=165  ,cap=_('&Keep indent')  ) # &s
#        ,dict(cid='!'   ,tp='bt'   ,t=5+120-28 ,l=5        ,w=80   ,cap=_('OK'),  props='1') #     default
#        ,dict(cid='-'   ,tp='bt'   ,t=5+120-28 ,l=5+80+5   ,w=80   ,cap=_('Cancel')        )
#        ],    dict(marg=str(margin)
#                  ,csgn=cmt_sgn
#                  ,svbl=True), focus_cid='marg')
#   if aid is None or aid=='-': return None

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
    pass;                      #log('rTx1, rTx2={}',(rTx1, rTx2)) if iflog(log4fun,_log4mod) else 0

    _rewrap(margin, cmt_sgn, save_bl, rTx1, rTx2, True)
   #def rewrap_sel_by_margin
        

def _replace_lines(_ed, r_bgn, r_end, newlines):
    """ Replace full lines in [r_bgn, r_end] to newlines """
    if app.app_api_version()<'1.0.187': return app.msg_status(_('Need update application'))
    lines_n     = _ed.get_line_count()
    pass;                      #log('lines_n, r_bgn, r_end, newlines={}',(lines_n, r_bgn, r_end, newlines)) if iflog(log4fun,_log4mod) else 0
    if r_end < lines_n-1:
        # Replace middle lines
        pass;                  #log('middle',()) if iflog(log4fun,_log4mod) else 0
        _ed.delete(0,r_bgn, 0,1+r_end)
        _ed.insert(0,r_bgn, newlines+'\n')
    else:
        # Replace final lines
        pass;                  #log('final',()) if iflog(log4fun,_log4mod) else 0
        _ed.delete(0,r_bgn, 0,lines_n)
        _ed.insert(0,r_bgn, newlines)
   #def _replace_lines
