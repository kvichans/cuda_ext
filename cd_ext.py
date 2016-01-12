''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '0.9.3 2016-01-12'
ToDo: (see end of file)
'''

import  re, os
import  cudatext        as app
from    cudatext    import ed
import  cudatext_cmd    as cmds
import  cudax_lib       as apx
from    cudax_lib   import log

# Localization
ONLY_SINGLE_CRT         = "{} doesn't work with multi-carets"
ONLY_FOR_NO_SEL         = "{} works when no selection"
NO_PAIR_BRACKET         = "Cannot find matching bracket for '{}'"
FIND_FAIL_FOR_STR       = "Cannot find: {}"
NO_FILE_FOR_OPEN        = "Cannot open: {}"

pass;                           # Logging
pass;                          #from pprint import pformat
pass;                          #pfrm15=lambda d:pformat(d,width=15)
pass;                           LOG = (-2==-2)  # Do or dont logging.

def _file_open(op_file):
    if not app.file_open(op_file):
        return None
    for h in app.ed_handles(): 
        op_ed   = app.Editor(h)
        if os.path.samefile(op_file, op_ed.get_filename()):
            return op_ed
    return None
   #def _file_open
   
class Command:
    def on_console_nav(self, ed_self, text):
        pass;                  #LOG and log('text={}',text)
        match   = re.match('.*File "([^"]+)", line (\d+)', text)    ##?? variants?
        if match is None:
            return
        op_file =     match.group(1)
        op_line = int(match.group(2))-1
        pass;                  #LOG and log('op_line, op_file={}',(op_line, op_file))
        if not os.path.exists(op_file):
            return app.msg_status(NO_FILE_FOR_OPEN.format(op_file))
        op_ed   = _file_open(op_file)
        op_ed.focus()
        op_ed.set_caret(0, op_line)
   #def on_console_nav
   
    def add_indented_line_above(self):
        ed.cmd(cmds.cCommand_KeyUp)
        ed.cmd(cmds.cCommand_KeyEnd)
        ed.cmd(cmds.cCommand_KeyEnter)
       #def add_indented_line_above
    def add_indented_line_below(self):
        ed.cmd(cmds.cCommand_KeyEnd)
        ed.cmd(cmds.cCommand_KeyEnter)
       #def add_indented_line_below

    def paste_to_1st_col(self):
        ''' Paste from clipboard without replacement caret/selection
                but only insert before current line
        ''' 
        pass;                  #LOG and log('')
        clip    = app.app_proc(app.PROC_GET_CLIP, '')
        if not clip:    return
        clip    = clip.replace('\r\n', '\n').replace('\r', '\n')
        if not (clip[-1] in '\r\n'):
            clip= clip + '\n'
        rnews   = clip.count('\n')
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format('Command'))
        (cCrt, rCrt, cEnd, rEnd)    = crts[0]
        r4ins   = min(rCrt, rCrt if -1==rEnd else rEnd)
        ed.insert(0, r4ins, clip)
        rCrtN   = rCrt+ rnews
        rEndN   = rEnd+(rnews if -1!=rEnd else 0)
        pass;                  #LOG and log('(rCrtN, rEndN)={}',(rCrtN, rEndN))
        ed.set_caret(cCrt, rCrtN
                    ,cEnd, rEndN)
        pass;                   return  ##??
        for icrt, (cCrt, rCrt, cEnd, rEnd) in reversed(list(enumerate(crts))):
#       for icrt, (cCrt, rCrt, cEnd, rEnd) in enumerate(crts):
            pass;              #LOG and log('icrt, (cCrt, rCrt, cEnd, rEnd), rnews={}',(icrt, (cCrt, rCrt, cEnd, rEnd), rnews))
            rCrtA   = rCrt+rnews*icrt
            rEndA   = rEnd+rnews*icrt if -1!=rEnd else -1
            r4ins   = min(rCrt, rCrt if -1==rEnd else rEnd)
            pass;              #LOG and log('(rCrtA, rEndA), r4ins={}',((rCrtA, rEndA), r4ins))
            ed.insert(0, r4ins, clip)
            rCrtN   = rCrt+ rnews
            rEndN   = rEnd+(rnews if -1!=rEnd else 0)
            pass;              #LOG and log('(rCrtN, rEndN)={}',(rCrtN, rEndN))
            ed.set_caret(cCrt, rCrtN
                        ,cEnd, rEndN
                        ,app.CARET_SET_INDEX+icrt)
           #for
       #def paste_to_1st_col

#   def find_cb_string(self, updn, bgn_crt_fin='crt'):
#       ''' Find clipboard value in text.
#           Params
#               updn            'up'|'dn' - direction
#               bgn_crt_fin     'bgn'|'crt'|'fin' - start point
#       '''
#       clip    = app.app_proc(app.PROC_GET_CLIP, '')
#       if ''==clip:    return
#       clip    = clip.replace('\r\n', '\n').replace('\r', '\n')
#       pass;                  #LOG and log('clip={}',repr(clip))
#       crts    = ed.get_carets()
#       if len(crts)>1:
#           return app.msg_status(ONLY_SINGLE_CRT.format('Command'))
#       # Prepare bgn-, crt-, fin-point
#       (cBgn, rBgn)    = (0, 0)
#       (cCrt, rCrt
#       ,cEnd, rEnd)    = crts[0]
#       lst_line_ind    = ed.get_line_count()-1
#       lst_line        = ed.get_text_line(lst_line_ind)
#       (cFin, rFin)    = (max(0, len(lst_line)-1), lst_line_ind)
#       if bgn_crt_fin=='crt':
#           # Some cases for natural (not wrap) find
#           if updn=='dn' and (cFin, rFin) == (cCrt, rCrt):
#               # Caret at finish - immediately find from start
#               return self.find_cb_string(updn, bgn_crt_fin='bgn')
#           if updn=='up' and (cBgn, rBgn) == (cCrt, rCrt):
#               # Caret at start - immediately find from finish
#               return self.find_cb_string(updn, bgn_crt_fin='fin')
#           if updn=='dn' and (cBgn, rBgn) == (cCrt, rCrt):
#               # Caret already at start - switch wrap off
#               bgn_crt_fin = 'bgn'
#           if updn=='up' and (cFin, rFin) == (cCrt, rCrt):
#               # Caret already at finish - switch wrap off
#               bgn_crt_fin = 'fin'
#       (cPnt, rPnt
#       ,cEnd, rEnd)    = apx.icase(False,0
#                           ,bgn_crt_fin=='bgn', (cBgn, rBgn, cBgn, rBgn)
#                           ,bgn_crt_fin=='crt', (cCrt, rCrt, cEnd, rEnd)
#                           ,bgn_crt_fin=='fin', (cFin, rFin, cFin, rFin)
#                           )
#       # Main part
#       if '\n' not in clip:
#           # 1) Find inside each line
#           row     = rPnt
#           line    = ed.get_text_line(row)
#           pos     = line.find(clip, cPnt) if updn=='dn' else line.rfind(clip, 0, cPnt)
#           while -1==pos:
#               row     = apx.icase(updn=='dn', row+1,   updn=='up', row-1,   -1)
#               if row<0 or row==ed.get_line_count():
#                   break #while
#               line    = ed.get_text_line(row)
#               pos     = line.find(clip) if updn=='dn' else line.rfind(clip)
#           if False:pass
#           elif -1==pos  and bgn_crt_fin!='crt':
#               return app.msg_status(FIND_FAIL_FOR_STR.format(clip))
#           elif -1==pos:#and bgn_crt_fin=='crt'
#               # Wrap!
#               return self.find_cb_string(updn, bgn_crt_fin=apx.icase(updn=='dn', 'bgn', 'fin'))
#           elif updn=='dn':
#               ed.set_caret(pos+len(clip), row, pos, row)
#           elif updn=='up':
#               ed.set_caret(pos, row, pos+len(clip), row)
#           return
#       # 2) Find m-line
#       pass;                  #LOG and log('')
#       clpls   = clip.split('\n')
#       pass;                  #LOG and log('clpls={}',(clpls))
#       clip    = repr(clip)
#       if False:pass
#       elif updn=='dn':
#           found   = False
#           row     = max(rPnt, rEnd if rEnd!=-1 else rPnt)
#           if row+len(clpls) < ed.get_line_count():
#               txtls   = [ed.get_text_line(r) for r in range(row, row+len(clpls))]
#               pass;          #LOG and log('txtls={}',(txtls))
#               while True:
#                   if self._find_cb_string_included_mlines(txtls, clpls):
#                       # Found!
#                       found   = True
#                       break #while
#                   row     = row+1
#                   pass;          #LOG and log('row={}',(row))
#                   if row+len(clpls) >= ed.get_line_count():
#                       pass;  #LOG and log('nfnd12',)
#                       break #while
#                   txtls   = txtls[1:]+[ed.get_text_line(row+len(clpls)-1)]
#                   pass;      #LOG and log('txtls={}',(txtls))
#                  #while
#           if False:pass
#           elif not found  and bgn_crt_fin!='crt':
#               return app.msg_status(FIND_FAIL_FOR_STR.format(clip))
#           elif not found:#and bgn_crt_fin=='crt'
#               # Wrap!
#               return self.find_cb_string(updn, bgn_crt_fin=apx.icase(updn=='dn', 'bgn', 'fin'))
#           ed.set_caret(len(clpls[-1]), row+len(clpls)-1, len(txtls[0])-len(clpls[0]), row)
#       elif updn=='up':
#           found   = False
#           row     = min(rPnt, rEnd if rEnd!=-1 else rPnt)
#           if row-len(clpls)+1 >= 0:
#               txtls   = [ed.get_text_line(r) for r in range(row-len(clpls)+1, row+1)]
#               pass;          #LOG and log('txtls={}',(txtls))
#               while True:
#                   if self._find_cb_string_included_mlines(txtls, clpls):
#                       # Found!
#                       found   = True
#                       break #while
#                   row     = row-1
#                   pass;          #LOG and log('row={}',(row))
#                   if row-len(clpls)+1 < 0:
#                       break #while
#                   txtls   = [ed.get_text_line(row-len(clpls)+1)]+txtls[:-1]
#                   pass;          #LOG and log('txtls={}',(txtls))
#                  #while
#           if False:pass
#           elif not found  and bgn_crt_fin!='crt':
#               return app.msg_status(FIND_FAIL_FOR_STR.format(clip))
#           elif not found:#and bgn_crt_fin=='crt'
#               # Wrap!
#               return self.find_cb_string(updn, bgn_crt_fin=apx.icase(updn=='dn', 'bgn', 'fin'))
#           ed.set_caret(len(clpls[-1]), row, len(txtls[0])-len(clpls[0]), row-len(clpls)+1)
#      #def find_cb_string
#   def _find_cb_string_included_mlines(self, txtls, clpls):
#       if len(txtls)!=len(clpls):
#           pass;              #LOG and log('fal l#l ',)
#           return False
#       if not  txtls[0].endswith(   clpls[0]):
#           pass;              #LOG and log('fal ends t,c={}',(txtls[0], clpls[0]))
#           return False
#       if not  txtls[-1].startswith(clpls[-1]):
#           pass;              #LOG and log('fal strt t,c={}',(txtls[-1], clpls[-1]))
#           return False
#       for ind in range(1, len(txtls)-1):
#           if txtls[ind] !=         clpls[ind]:
#               pass;          #LOG and log('fal4 eq ind={} t,c={}',ind, (txtls[0], clpls[0]))
#               return False
#       pass;                  #LOG and log('tru',)
#       return True
#      #def _find_cb_string_included_mlines
    def find_cb_string_next(self):
        self.find_cb_by_cmd('dn')
       #self.find_cb_string('dn')
    def find_cb_string_prev(self):
        self.find_cb_by_cmd('up')
       #self.find_cb_string('up')
    def find_cb_by_cmd(self, updn):
        clip    = app.app_proc(app.PROC_GET_CLIP, '')
        if ''==clip:    return
        clip    = clip.replace('\r\n', '\n').replace('\r', '\n')    ##??
        ed.cmd(cmds.cmd_FinderAction, chr(1).join([]
            +['findprev' if updn=='up' else 'findnext']
            +[clip]
            +['']
            +['fa']  # f - from caret,  a - wrapped
        ))
       #def find_cb_by_cmd

    def replace_all_sel_to_cb(self):
        crts    = ed.get_carets()
        if len(crts)!=1: return
        seltext = ed.get_text_sel()
        if not seltext: return
        clip    = app.app_proc(app.PROC_GET_CLIP, '')
        ed.cmd(cmds.cmd_FinderAction, chr(1).join([]
            +['repall']
            +[seltext]
            +[clip]
            +['a']  # a - wrapped
        ))
       #def replace_all_sel_to_cb
    
    def open_selected(self):
        pass;                  #LOG and log('ok',)
        bs_dir      = os.path.dirname(ed.get_filename())
        crts        = ed.get_carets()
        if len(crts)!=1: return
        (cCrt, rCrt
        ,cEnd, rEnd)= crts[0]
        pointed = ed.get_text_sel()
        if not pointed:
            # Empty selection, will use word/term
            line    = ed.get_text_line(rCrt)
            (pointed
            ,where) = get_word_or_quoted(line, cCrt)
        pass;                  #LOG and log('pointed={}',pointed)
        if not pointed: return
        op_file     = os.path.join(bs_dir, pointed)
        if not os.path.isfile(op_file):
            return app.msg_status(NO_FILE_FOR_OPEN.format(op_file))
        op_ed       = _file_open(op_file)
        if not op_ed:
            return app.msg_status(NO_FILE_FOR_OPEN.format(op_file))
        op_ed.focus()
       #def open_selected
    
    def _activate_tab(self, group, tab_ind):
        pass;                  #LOG and log('')
        for h in app.ed_handles():
            edH = app.Editor(h)
            if ( group  ==edH.get_prop(app.PROP_INDEX_GROUP)
            and  tab_ind==edH.get_prop(app.PROP_INDEX_TAB)):
                edH.focus() 
                return True
        return False
       #def _activate_tab
    def _activate_last_tab(self, group):
        pass;                  #LOG and log('')
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
    def _activate_near_tab(self, gap):
        pass;                  #LOG and log('gap={}',gap)
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

    def _move_splitter(self, what, factor):
        ''' Move one of splitters
            Params:
                what    Which splitter and changing width or height 
                            'into'          - into tab, direction as is
                            'left'          - tree
                            'bott'          - console/output/...
                            'main'          - top-left group, 
                                                width if has right neighbor
                                                else height
                            'curr'          - active group, 
                                                self     width  if has right  neighbor
                                                neighbor width  if has left   neighbor
                                                self     height if has bottom neighbor
                                                neighbor height if has upper  neighbor
                factor  Multiplier for relation pos of splitter.
                            NewPos  = int(factor * OldPos)
        '''
        pass;                  #LOG and log('what, factor={}',(what, factor))
        id_splt     = ''
        pos_old     = 0
        prn_size    = 0
        if False:pass
        elif what=='into':  # In tab 
            return
        
        elif what=='left':  # Tree
            id_splt     = 'L'
        elif what=='bott':  # Bottom
            id_splt     = 'B'
        
        else:               # Groups
            # 2HORZ     0 G1 1
            # 2VERT     0
            #           G1
            #           1
            # 3HORZ     0 G1 1 G2 2
            # 3VERT     0
            #           G1
            #           1
            #           G2
            #           2
            # 3PLUS     0 G3 1 
            #                G2 
            #                2 
            # 4HORZ     0 G1 1 G2 2 G3 3
            # 4VERT     0
            #           G1
            #           1
            #           G2
            #           2
            #           G3
            #           3
            # 4GRID     0 G1 1
            #           G3
            #           2 G2 3
            # 6GRID     0 G1 1 G2 2
            #           G3
            #           3 G1 4 G2 5
            grouping    = app.app_proc(app.PROC_GET_GROUPING, '')
            cur_grp     = ed.get_prop(app.PROP_INDEX_GROUP)
            if False:pass
            elif grouping==app.GROUPS_ONE:
                return      # No splitter

            elif (what=='main' 
            and   grouping!=app.GROUPS_3PLUS):      id_splt = 'G1'
            elif (what=='main' 
            and   grouping==app.GROUPS_3PLUS):      id_splt = 'G3'

            #     what=='curr'
            elif cur_grp==0:
                if False:pass
                elif grouping==app.GROUPS_2HORZ:    id_splt = 'G1'  # w-self
                elif grouping==app.GROUPS_2VERT:    id_splt = 'G1'  # h-self
                elif grouping==app.GROUPS_3HORZ:    id_splt = 'G1'  # w-self
                elif grouping==app.GROUPS_3VERT:    id_splt = 'G1'  # h-self
                elif grouping==app.GROUPS_3PLUS:    id_splt = 'G3'  # w-self
                elif grouping==app.GROUPS_4HORZ:    id_splt = 'G1'  # w-self
                elif grouping==app.GROUPS_4VERT:    id_splt = 'G1'  # h-self
                elif grouping==app.GROUPS_4GRID:    id_splt = 'G1'  # w-self
                elif grouping==app.GROUPS_6GRID:    id_splt = 'G1'  # w-self

            elif cur_grp==1:
                if False:pass
                elif grouping==app.GROUPS_2HORZ:    id_splt ='-G1'  # w-left
                elif grouping==app.GROUPS_2VERT:    id_splt ='-G1'  # h-top
                elif grouping==app.GROUPS_3HORZ:    id_splt = 'G2'  # w-self
                elif grouping==app.GROUPS_3VERT:    id_splt = 'G2'  # h-self
                elif grouping==app.GROUPS_3PLUS:    id_splt = 'G2'  # h-self
                elif grouping==app.GROUPS_4HORZ:    id_splt = 'G2'  # w-self
                elif grouping==app.GROUPS_4VERT:    id_splt = 'G2'  # h-self
                elif grouping==app.GROUPS_4GRID:    id_splt ='-G1'  # w-left
                elif grouping==app.GROUPS_6GRID:    id_splt = 'G2'  # w-self

            elif cur_grp==2:
                if False:pass
                elif grouping==app.GROUPS_3HORZ:    id_splt ='-G2'  # w-left
                elif grouping==app.GROUPS_3VERT:    id_splt ='-G2'  # h-top
                elif grouping==app.GROUPS_3PLUS:    id_splt ='-G2'  # h-top
                elif grouping==app.GROUPS_4HORZ:    id_splt = 'G3'  # w-self
                elif grouping==app.GROUPS_4VERT:    id_splt = 'G3'  # h-self
                elif grouping==app.GROUPS_4GRID:    id_splt = 'G2'  # w-self
                elif grouping==app.GROUPS_6GRID:    id_splt ='-G2'  # w-left

            elif cur_grp==3:
                if False:pass
                elif grouping==app.GROUPS_4HORZ:    id_splt ='-G3'  # w-left
                elif grouping==app.GROUPS_4VERT:    id_splt ='-G3'  # h-top
                elif grouping==app.GROUPS_4GRID:    id_splt ='-G2'  # w-left
                elif grouping==app.GROUPS_6GRID:    id_splt = 'G1'  # w-self

            elif cur_grp==4:
                if False:pass
                elif grouping==app.GROUPS_6GRID:    id_splt = 'G2'  # w-self

            elif cur_grp==5:
                if False:pass
                elif grouping==app.GROUPS_6GRID:    id_splt ='-G2'  # w-left

            else:
                return
        if id_splt[0]=='-':
            id_splt = id_splt[1:]
            factor  = 2 - factor

        (vh, shown, pos_old, prn_size)  = app.app_proc(app.PROC_GET_SPLIT, id_splt)
        pass;                  #LOG and log('id_splt, vh, shown, pos_old, prn_size={}',(id_splt, vh, shown, pos_old, prn_size))
        if not shown:           return
        pos_new     = int(factor * pos_old) 
        pass;                  #LOG and log('pos_new={}',(pos_new))
        pos_new     = max(100, min(prn_size-100, pos_new))
        pass;                  #LOG and log('pos_new={}',(pos_new))
        if pos_new==pos_old:    return
        app.app_proc(app.PROC_SET_SPLIT, '{};{}'.format(id_splt, pos_new))
       #def _move_splitter

    def jump_to_matching_bracket(self):
        ''' Jump single (only!) caret to matching bracket.
            Pairs: [] {} () <> «»
        '''
        pass;                  #LOG and log('')
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format('Command'))
        (cCrt, rCrt, cEnd, rEnd)    = crts[0]
        if cEnd!=-1:
            return app.msg_status(ONLY_FOR_NO_SEL.format('Command'))

        (c_opn, c_cls
        ,col, row)  = find_matching_char(ed, cCrt, rCrt)

        if c_opn!='' and -1!=col:
            pass;              #LOG and log('set_caret(col, row)={}', (col, row))
            ed.set_caret(col, row)
        else:
            return app.msg_status(NO_PAIR_BRACKET.format(c_opn))
       #def jump_to_matching_bracket

   #class Command

def find_matching_char(ed4find, cStart, rStart, opn2cls={'[':']', '{':'}', '(':')', '<':'>', '«':'»'}):
    ''' Find matching (pair) char for char from position (cStart,rStart) (or prev) 
    '''
    cls2opn = {c:o for o,c in opn2cls.items()}
    
    crt_line=  ed4find.get_text_line(rStart)
    # Is there any bracket AFTER caret?
    c_aft   = crt_line[cStart]   if cStart<len(crt_line) else ' '
    c_bfr   = crt_line[cStart-1] if cStart>0             else ' '
    pass;                      #LOG and log('c_bfr, c_aft={}', (c_bfr, c_aft))

    if False:pass
    elif c_aft in opn2cls: (c_opn, c_cls, col) = (c_aft, opn2cls[c_aft], cStart+1)
    elif c_aft in cls2opn: (c_opn, c_cls, col) = (c_aft, cls2opn[c_aft], cStart-1)
    elif c_bfr in opn2cls: (c_opn, c_cls, col) = (c_bfr, opn2cls[c_bfr], cStart  )
    elif c_bfr in cls2opn: (c_opn, c_cls, col) = (c_bfr, cls2opn[c_bfr], cStart-2)
    else: return (c_aft, '', -1, -1)

    to_end  = c_opn in opn2cls
    line    = crt_line
    row     = rStart
    pass;                      #LOG and log('c_opn,c_cls,to_end,col={}', (c_opn,c_cls,to_end,col))
    cnt     = 1
    while True:
        for pos in (range(col, len(line)) if to_end else 
                    range(col, -1, -1)):
            c   = line[pos]
            if False:pass
            elif c==c_opn:
                cnt     = cnt+1
            elif c==c_cls:
                cnt     = cnt-1
            else:
                continue # for pos
            pass;              #LOG and log('line, pos, c, cnt={}', (line, pos, c, cnt))
            if 0==cnt:
                # Found!
                col     = pos
                break #for pos 
        if 0==cnt:
            break #while
        if to_end:
            row     = row+1
            if row==ed4find.get_line_count():
                pass;          #LOG and log('not found')
                break #while
            line    = ed4find.get_text_line(row)
            col     = 0
        else:
            if row==0:
                pass;          #LOG and log('not found')
                break #while
            row     = row-1
            line    = ed4find.get_text_line(row)
            col     = len(line)-1
       #while
    return (c_opn, c_cls, col, row) if cnt==0 else (c_opn, c_cls, -1, -1)
   #def find_matching_char

def get_word_or_quoted(text, start, not_word_chars='[](){}', quot_chars="'"+'"'):      # '"
    ''' Find word or 'smth' or "smth" around start.
        Return      (found, pos_of_found)
    '''
    if not text or not(0<=start<=len(text)):   return ('', -1)
    text        = ' '+text+' '
    start       = start+1
    bgn, end    = -1, -1
    left_cond   = ' '
    # Backward
    pos         = start-1
    while 0<=pos:
        c       = text[pos]
        if c.isspace() or c in not_word_chars:
            left_cond   = ' '
            bgn         = pos+1
            break
        if c in quot_chars:
            left_cond   = c
            bgn         = pos+1
            break
        pos    -= 1
    # Forward
    pos         = start
    while pos<len(text):
        c       = text[pos]
        if left_cond==' ' and (c.isspace() or c in not_word_chars):
            end         = pos
            break
        if left_cond!=' ' and c in quot_chars:
            end         = pos
            break
        pos    += 1
    
    return (text[bgn:end], bgn-1) if bgn!=-1 and end!=-1 else ('', -1)
   #def get_word_or_quoted

'''
ToDo
[+][kv-kv][20nov15] Вставить строку с отступом под/над текущей
[+][kv-kv][20nov15] Activate tab #1, #2, ..., #9 Activate tab on 2nd group #1, #2, ..., #9
[+][kv-kv][20nov15] Paste from clipboard, to 1st column: paste_to_1st_col
[?][kv-kv][20nov15] Paste from clipboard, to 1st column for m-carets
[+][kv-kv][20nov15] Find string from clipboard - next/prev: find_cb_string_next
[+][kv-kv][20nov15] Jump to matching bracket: jump_to_matching_bracket
[-][kv-kv][20nov15] CopyTerm, ReplaceTerm
[-][kv-kv][20nov15] Comment/uncomment before cur term (or fix col?)
[+][kv-kv][24nov15] Wrap for "Find string from clipboard"
[ ][kv-kv][25nov15] Replace all as selected to cb-string: replace_all_sel_to_cb
[+][kv-kv][25nov15] Open selected file: open_selected
[+][kv-kv][25nov15] Catch on_console_nav
[ ][kv-kv][26nov15] Scroll on_console_nav, Find*
[ ][at-kv][09dec15] Refactor: find_pair
[ ][kv-kv][15dec15] Find cb-string via cmd_FinderAction (for use next/prev after)
'''
