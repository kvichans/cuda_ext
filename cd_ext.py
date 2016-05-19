''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '1.1.0 2016-05-19'
ToDo: (see end of file)
'''

import  re, os, sys, json
import  cudatext            as app
from    cudatext        import ed
import  cudatext_cmd        as cmds
import  cudax_lib           as apx
from    cudax_lib       import log
from    .cd_plug_lib    import *

FROM_API_VERSION= '1.0.119'

# I18N
_       = get_translation(__file__)

ONLY_SINGLE_CRT     = _("{} doesn't work with multi-carets")
ONLY_FOR_NO_SEL     = _("{} works when no selection")
NO_PAIR_BRACKET     = _("Cannot find matching bracket for '{}'")
FIND_FAIL_FOR_STR   = _("Cannot find: {}")
NO_FILE_FOR_OPEN    = _("Cannot open: {}")
NEED_UPDATE         = _("Need update CudaText")
EMPTY_CLIP          = _("Empty value in clipboard")
NO_LEXER            = _("No lexer")
#UPDATE_FILE         = _("File '{}' is updated")
USE_NOT_EMPTY       = _("Set not empty values")
ONLY_FOR_ML_SEL     = _("{} works with multiline selection")
NO_SPR_IN_LINES     = _("No seperator '{}' in selected lines")
DONT_NEED_CHANGE    = _("Text change not needed")

pass;                           # Logging
pass;                          #from pprint import pformat
pass;                          #pfrm15=lambda d:pformat(d,width=15)
pass;                           LOG = (-2==-2)  # Do or dont logging.
pass;                           ##!! waits correction

GAP     = 5

def _file_open(op_file):
    if not app.file_open(op_file):
        return None
    for h in app.ed_handles(): 
        op_ed   = app.Editor(h)
        if op_ed.get_filename() and os.path.samefile(op_file, op_ed.get_filename()):
            return op_ed
    return None
   #def _file_open

#############################################################
class Tree_cmds:
    @staticmethod
    def tree_path_to_status():
        path_l, gap = Tree_cmds._get_best_tree_path(ed.get_carets()[0][1])
        if not path_l:  return
        ID_TREE = app.app_proc(app.PROC_SIDEPANEL_GET_CONTROL, 'Tree')
        id_sel  = app.tree_proc(ID_TREE, app.TREE_ITEM_GET_SELECTED)
        id_need = path_l[-1][0]
        if id_need != id_sel:
            app.tree_proc(ID_TREE, app.TREE_ITEM_SELECT, id_need)
        path    = ' // '.join([cap.rstrip(':')[:40] for (nid,cap) in path_l])
        if gap==0:  return app.msg_status(path)
        app.msg_status(f('[{:+}] {}', gap, path))
       #def tree_path_to_status
   
    @staticmethod
    def set_nearest_tree_node():
        path_l, gap = Tree_cmds._get_best_tree_path(ed.get_carets()[0][1])
        if not path_l:  return
        ID_TREE = app.app_proc(app.PROC_SIDEPANEL_GET_CONTROL, 'Tree')
        app.tree_proc(ID_TREE, app.TREE_ITEM_SELECT, path_l[-1][0])
       #def set_nearest_tree_node
   
    @staticmethod
    def _get_best_tree_path(row):
        """ Find node-path nearext to row: all nodes cover row or are all above/below nearest.
            Return
                [(widest_node_id,cap), (node_id,cap), ..., (smallest_node_id,cap)], gap
                    list can be empty
                    gap:  0 if row is covered
                         >0 if nearest node below
                         <0 if nearest node above
        """
        ID_TREE = app.app_proc(app.PROC_SIDEPANEL_GET_CONTROL, 'Tree')
        INF     = 0xFFFFFFFF
        NO_ID   = -1
        def best_path(id_prnt, prnt_cap=''):
            rsp_l   = [] 
            kids    = app.tree_proc(ID_TREE, app.TREE_ITEM_ENUM, id_prnt)
            pass;                  #LOG and log('>>id_prnt, prnt_cap, kids={}',(id_prnt, prnt_cap, len(kids) if kids else 0))
            if kids is None:
                pass;              #LOG and log('<<no kids',())
                return [], INF
            row_bfr, kid_bfr, cap_bfr = -INF, NO_ID, ''
            row_aft, kid_aft, cap_aft = +INF, NO_ID, ''
            for kid, cap in kids:
                pass;              #LOG and log('kid, cap={}',(kid, cap))
                cMin, rMin, \
                cMax, rMax  = app.tree_proc(ID_TREE, app.TREE_ITEM_GET_SYNTAX_RANGE, kid)
                pass;              #LOG and log('? kid,cap, rMin,rMax,row={}',(kid,cap, rMin,rMax,row))
                if False:pass
                elif rMin<=row<=rMax:   # Cover!
                    sub_l, gap_sub  = best_path(kid, cap)
                    pass;          #LOG and log('? sub_l, gap_sub={}',(sub_l, gap_sub))
                    if gap_sub == 0:    # Sub-kid also covers
                        pass;      #LOG and log('+ sub_l={}',(sub_l))
                        rsp_l   = [(kid, cap)] + sub_l
                    else:               # The kid is best
                        pass;      #LOG and log('0 ',())
                        rsp_l   = [(kid, cap)]
                    pass;          #LOG and log('<<! rsp_l={}',(rsp_l))
                    return rsp_l, 0
                elif row_bfr                  < rMax            < row:
                    row_bfr, kid_bfr, cap_bfr = rMax, kid, cap
                    pass;          #LOG and log('< row_bfr, kid_bfr, cap_bfr={}',(row_bfr, kid_bfr, cap_bfr))
                elif row_aft                  > rMin            > row:
                    row_aft, kid_aft, cap_aft = rMin, kid, cap
                    pass;          #LOG and log('> row_aft, kid_aft, cap_aft={}',(row_aft, kid_aft, cap_aft))
               #for kid
            pass;                  #LOG and log('? row_bfr, kid_bfr, cap_bfr={}',(row_bfr, kid_bfr, cap_bfr))
            pass;                  #LOG and log('? row_aft, kid_aft, cap_aft={}',(row_aft, kid_aft, cap_aft))
            pass;                  #LOG and log('? abs(row_bfr-row), abs(row_aft-row)={}',(abs(row_bfr-row), abs(row_aft-row)))
            kid_x, cap_x, gap_x = (kid_bfr, cap_bfr, row_bfr-row) \
                                if abs(row_bfr-row) <= abs(row_aft-row) else \
                                  (kid_aft, cap_aft, row_aft-row)
            pass;                  #LOG and log('kid_x, cap_x, gap_x={}',(kid_x, cap_x, gap_x))
            sub_l, gap_sub  = best_path(kid_x, cap_x)
            pass;                  #LOG and log('? sub_l,gap_sub ?? gap_x={}',(sub_l, gap_sub, gap_x))
            if abs(gap_sub) <= abs(gap_x):  # Sub-kid better
                rsp_l  = [(kid_x, cap_x)] + sub_l
                pass;              #LOG and log('<<sub bt: rsp_l, gap_sub={}',(rsp_l, gap_sub))
                return rsp_l, gap_sub
            # The kid is best
            rsp_l   = [(kid_x, cap_x)]
            pass;                  #LOG and log('<<bst: rsp_l, gap_x={}',(rsp_l, gap_x))
            return rsp_l, gap_x
           #def descent
        lst, gap= best_path(0)
        pass;                      #LOG and log('lst, gap={}',(lst, gap))
        return lst, gap
       #def _get_best_tree_path
   #class Tree_cmds

#############################################################
class Tabs_cmds:
    @staticmethod
    def _activate_tab(group, tab_ind):
        pass;                      #LOG and log('')
        for h in app.ed_handles():
            edH = app.Editor(h)
            if ( group  ==edH.get_prop(app.PROP_INDEX_GROUP)
            and  tab_ind==edH.get_prop(app.PROP_INDEX_TAB)):
                edH.focus() 
                return True
        return False
       #def _activate_tab

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def move_tab():
        old_pos = ed.get_prop(app.PROP_INDEX_TAB)
        new_pos = app.dlg_input('New position', str(old_pos+1))
        if new_pos is None: return
        new_pos = max(1, int(new_pos))
        ed.set_prop(app.PROP_INDEX_TAB, str(new_pos-1))
       #def move_tab

    @staticmethod
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
   #class Tabs_cmds

#############################################################
class Jumps_cmds:
    @staticmethod
    def jump_to_matching_bracket():
        ''' Jump single (only!) caret to matching bracket.
            Pairs: [] {} () <> «»
        '''
        pass;                      #LOG and log('')
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format('Command'))
        (cCrt, rCrt, cEnd, rEnd)    = crts[0]
        if cEnd!=-1:
            return app.msg_status(ONLY_FOR_NO_SEL.format('Command'))

        (c_opn, c_cls
        ,col, row)  = find_matching_char(ed, cCrt, rCrt)

        if c_opn!='' and -1!=col:
            pass;                  #LOG and log('set_caret(col, row)={}', (col, row))
            ed.set_caret(col, row)
        else:
            return app.msg_status(NO_PAIR_BRACKET.format(c_opn))
       #def jump_to_matching_bracket

    @staticmethod
    def scroll_to_center():
       #wraped      = apx.get_opt('wrap_mode', False, apx.CONFIG_LEV_FILE)
       #last_on_top = apx.get_opt('show_last_line_on_top', False)
        txt_lines   = ed.get_line_count()
        old_top_line= ed.get_prop(app.PROP_LINE_TOP) if app.app_api_version()>='1.0.126' else ed.get_top()
        scr_lines   = ed.get_prop(app.PROP_VISIBLE_LINES)
        crt_line    = ed.get_carets()[0][1]
        
        new_top_line= crt_line - int(scr_lines/2)
        new_top_line= max(new_top_line, 0)
        new_top_line= min(new_top_line, txt_lines-1)
        pass;                      #LOG and log('cur, old, new, scr={}',(crt_line, old_top_line, new_top_line, scr_lines))
        
        if new_top_line!=old_top_line:
            if app.app_api_version()>='1.0.126':
                ed.set_prop(app.PROP_LINE_TOP, str(new_top_line))
            else: # old
                ed.set_top(new_top_line)
       #def scroll_to_center
   #class Jumps_cmds

#############################################################
class Nav_cmds:
    @staticmethod
    def on_console_nav(ed_self, text):
        pass;                      #LOG and log('text={}',text)
        match   = re.match('.*File "([^"]+)", line (\d+)', text)    ##?? variants?
        if match is None:
            return
        op_file =     match.group(1)
        op_line = int(match.group(2))-1
        pass;                      #LOG and log('op_line, op_file={}',(op_line, op_file))
        if not os.path.exists(op_file):
            return app.msg_status(NO_FILE_FOR_OPEN.format(op_file))
        op_ed   = _file_open(op_file)
        op_ed.focus()
        op_ed.set_caret(0, op_line)
       #def on_console_nav

    @staticmethod
    def _open_file_near(where='right'):
        cur_path= ed.get_filename()
        init_dir= os.path.dirname(cur_path) if cur_path else ''
        fls     = app.dlg_file(True, '*', init_dir, '')   # '*' - multi-select
        if not fls: return
        fls     = [fls] if isinstance(fls, str) else fls

        group   = ed.get_prop(app.PROP_INDEX_GROUP)
        tab_pos = ed.get_prop(app.PROP_INDEX_TAB)
        if False:pass
        elif where=='right':
            for fl in reversed(fls):
                app.file_open(fl, group)
                ed.set_prop(app.PROP_INDEX_TAB, str(1+tab_pos))
        elif where=='left':
            for fl in fls:
                app.file_open(fl, group)
                ed.set_prop(app.PROP_INDEX_TAB, str(tab_pos))
                tab_pos +=1
       #def open_file_near
    
    @staticmethod
    def nav_by_console_err():
        cons_out= app.app_log(app.LOG_CONSOLE_GET_LOG, '')
        fn      = ed.get_filename()
        if not fn:      return app.msg_status(_('Only for saved file'))
        fn_ln_re= f('File "{}", line ', fn).replace('\\','\\\\')+'(\d+)'
        pass;                      #LOG and log('fn_ln_re={}',fn_ln_re)
        mtchs   = list(re.finditer(fn_ln_re, cons_out, re.I))
        if not mtchs:   return app.msg_status(_('No filename in output: '+fn))
        mtch    = mtchs[-1]
        row     = int(mtch.group(1))-1
        pass;                      #LOG and log('row={}',row)
        ed.set_caret(0, row)
       #def nav_by_console_err

    @staticmethod
    def open_selected():
        pass;                      #LOG and log('ok',)
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
        pass;                      #LOG and log('pointed={}',pointed)
        if not pointed: return
        op_file     = os.path.join(bs_dir, pointed)
        op_row      = -1
        if not os.path.isfile(op_file) and \
           '(' in op_file:                                      #)
                # Try to split in 'path(row'                    #)
                mtch= re.search(r'(.*)\((\d+)', op_file)
                if mtch:
                    pointed, op_row = mtch.groups()
                    op_row          = int(op_row)
                    op_file         = os.path.join(bs_dir, pointed)
        if not os.path.isfile(op_file):
            return app.msg_status(NO_FILE_FOR_OPEN.format(op_file))
        op_ed       = _file_open(op_file)
        if not op_ed:
            return app.msg_status(NO_FILE_FOR_OPEN.format(op_file))
        op_ed.focus()
        if op_row!=-1:
            op_ed.set_caret(0, op_row)
       #def open_selected
   #class Nav_cmds

#############################################################
class Find_repl_cmds:
    @staticmethod
    def find_cb_by_cmd(updn):
        if app.app_api_version()<FROM_API_VERSION:  return app.msg_status(NEED_UPDATE)
        clip    = app.app_proc(app.PROC_GET_CLIP, '')
        if ''==clip:    return
        clip    = clip.replace('\r\n', '\n').replace('\r', '\n')    ##??
        user_opt= app.app_proc(app.PROC_GET_FIND_OPTIONS, '')
        # c - Case, r - RegEx,  w - Word,  f - From-caret,  a - Wrapp,  b - Back
        find_opt= 'f'
        find_opt= find_opt + ('c' if 'c' in user_opt else '')   # As user: Case
        find_opt= find_opt + ('w' if 'w' in user_opt else '')   # As user: Word
        find_opt= find_opt + ('a' if 'a' in user_opt else '')   # As user: Wrap
        ed.cmd(cmds.cmd_FinderAction, chr(1).join([]
            +['findprev' if updn=='up' else 'findnext']
            +[clip]
            +['']
            +[find_opt]
        ))
        app.app_proc(app.PROC_SET_FIND_OPTIONS, user_opt)
       #def find_cb_by_cmd

    @staticmethod
    def replace_all_sel_to_cb():
        if app.app_api_version()<FROM_API_VERSION:  return app.msg_status(NEED_UPDATE)
        crts    = ed.get_carets()
        if len(crts)>1: return app.msg_status(ONLY_SINGLE_CRT.format('Command'))
        seltext = ed.get_text_sel()
        if not seltext: return
        clip    = app.app_proc(app.PROC_GET_CLIP, '')
        user_opt= app.app_proc(app.PROC_GET_FIND_OPTIONS, '')
        # c - Case, r - RegEx,  w - Word,  f - From-caret,  a - Wrap
        find_opt= 'a'
        find_opt= find_opt + ('c' if 'c' in user_opt else '')   # As user: Case
        find_opt= find_opt + ('w' if 'w' in user_opt else '')   # As user: Word
        ed.lock()
        ed.cmd(cmds.cmd_FinderAction, chr(1).join([]
            +['repall']
            +[seltext]
            +[clip]
            +[find_opt]  # a - wrapped
        ))
        ed.unlock()
        app.app_proc(app.PROC_SET_FIND_OPTIONS, user_opt)
       #def replace_all_sel_to_cb
   #class Find_repl_cmds

#############################################################
class Insert_cmds:
    @staticmethod
    def add_indented_line_above():  ##!!
        ed.cmd(cmds.cCommand_KeyUp)
        ed.cmd(cmds.cCommand_KeyEnd)
        ed.cmd(cmds.cCommand_KeyEnter)
       #def add_indented_line_above
    @staticmethod
    def add_indented_line_below():  ##!!
        ed.cmd(cmds.cCommand_KeyEnd)
        ed.cmd(cmds.cCommand_KeyEnter)
       #def add_indented_line_below

    @staticmethod
    def paste_to_1st_col():
        ''' Paste from clipboard without replacement caret/selection
                but only insert before current line
        ''' 
        pass;                      #LOG and log('')
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
        pass;                      #LOG and log('(rCrtN, rEndN)={}',(rCrtN, rEndN))
        ed.set_caret(cCrt, rCrtN
                    ,cEnd, rEndN)
        pass;                   return  ##??
       #def paste_to_1st_col

    @staticmethod
    def paste_with_indent(where='above'): ##!!
        ''' Paste above/below with fitting indent of clip to indent of active line
            Param
                where   'above' Insert between this and prev line
                        'below' Insert between this and next line
                        'lazar' Insert between this and prev line 
                                    if caret before text else
                                normal insert 
        '''
        clip    = app.app_proc(app.PROC_GET_CLIP, '')
        pass;                      #LOG and log('clip={}',repr(clip))
        if not clip:        return app.msg_status(_('Empty clip'))
        if not clip.strip():return app.msg_status(_('No text in clip'))
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format('Command'))

        END_SIGNS = ['begin', '{', ':', 'then']   # }

        use_tab = not ed.get_prop(app.PROP_TAB_SPACES)  # apx.get_opt('tab_spaces')
        sps_tab = ' '*ed.get_prop(app.PROP_TAB_SIZE)    # apx.get_opt('tab_size')
        pass;                      #LOG and log('use_tab,sps_tab={}',(use_tab,sps_tab))

        (cCrt, rCrt, cEnd, rEnd) = crts[0]
        if cEnd!=-1:    return app.msg_status(_('Command works only if no selection'))
        r4ins   = rCrt  # min(rCrt, rCrt if -1==rEnd else rEnd)
        ln_tx   = ed.get_text_line(r4ins).rstrip()
        if where=='lazar':
            return
            
        if where=='below' and \
            any(map(lambda sign:ln_tx.lower().endswith(sign), END_SIGNS)):
            # Extra indent
            ln_tx = ('\t' if use_tab else sps_tab) + ln_tx
        
        # Fit clip
        lns_cl  = clip.splitlines()
        def replaces_spaces_atstart(s, what_s, with_s):
            ind_tx  = len(s) - len(s.lstrip())
            return s[:ind_tx].replace(what_s, with_s) + s[ind_tx:]
        if     use_tab and clip[0]==' ':
            # Replace spaces to tab in begining of each clip lines
            lns_cl  = [replaces_spaces_atstart(cl_ln, sps_tab, '\t')
                       for cl_ln in lns_cl]
            pass;                  #LOG and log('sp->tb lns_cl={}',(lns_cl))
        if not use_tab and clip[0]=='\t':
            # Replace tab to spaces in begining of each clip lines
            lns_cl  = [replaces_spaces_atstart(cl_ln, '\t', sps_tab)
                       for cl_ln in lns_cl]
            pass;                  #LOG and log('tb->sp lns_cl={}',(lns_cl))
        
        ind_ln  =      len(ln_tx) - len(ln_tx.lstrip())
        ind_cl  = min([len(cl_ln) - len(cl_ln.lstrip())
                       for cl_ln in lns_cl])
        pass;                      #LOG and log('ind_ln, ind_cl={}',(ind_ln, ind_cl))
        if False:pass
        elif ind_cl > ind_ln:
            # Cut clip lines
            lns_cl  = [cl_ln[  ind_cl - ind_ln:]
                       for cl_ln in lns_cl]
            pass;                  #LOG and log('cut lns_cl={}',(lns_cl))
        elif ind_ln > ind_cl:
            # Add to clip lines
            apnd    = ln_tx[0]*(ind_ln - ind_cl)
            lns_cl  = [apnd+cl_ln
                       for cl_ln in lns_cl]
            pass;                  #LOG and log('add lns_cl={}',(lns_cl))
        clip    = '\n'.join(lns_cl)
        clip    = clip+'\n' if clip[-1] not in '\n\r' else clip
        
        # Insert
        pass;                      #LOG and log('ln_tx={}',repr(ln_tx))
        pass;                      #LOG and log('clip={}',repr(clip))
        if where=='above':
            ed.insert(0, r4ins,   clip)
        else:
            ed.insert(0, r4ins+1, clip)
       #def paste_with_indent
    
    data4_align_in_lines_by_sep = ''
    @staticmethod
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
#       global data4_align_in_lines_by_sep
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format('Command'))
        (cCrt, rCrt
        ,cEnd, rEnd)    = crts[0]
        if rEnd==-1 or rEnd==rCrt:
            return app.msg_status(ONLY_FOR_ML_SEL.format('Command'))
        spr     = app.dlg_input('Enter separator string', Insert_cmds.data4_align_in_lines_by_sep)
        spr     = '' if spr is None else spr.strip()
        if not spr:
            return # Esc
        data4_align_in_lines_by_sep    = spr
        ((rTx1, cTx1)
        ,(rTx2, cTx2))  = apx.minmax((rCrt, cCrt), (rEnd, cEnd))
        ls_txt  = ed.get_text_substr(0,rTx1, 0,rTx2+(0 if 0==cEnd else 1))
        if spr not in ls_txt: 
            return app.msg_status(NO_SPR_IN_LINES.format(spr))
        lines   = ls_txt.splitlines()
        ln_poss = [(ln, ln.find(spr)) for ln in lines]
        max_pos =    max([p for (l,p) in ln_poss])
        if max_pos== min([p if p>=0 else max_pos for (l,p) in ln_poss]):
            return app.msg_status(DONT_NEED_CHANGE)
        nlines  = [ln       if pos==-1 or max_pos==pos else 
                   ln[:pos]+' '*(max_pos-pos)+ln[pos:]
                   for (ln,pos) in ln_poss
                  ]
        ed.delete(0,rTx1, 0,rTx2+(0 if 0==cEnd else 1))
        ed.insert(0,rTx1, '\n'.join(nlines)+'\n')
        ed.set_caret(0,rTx1+len(nlines), 0, rTx1)
       #def align_in_lines_by_sep
   #class Insert_cmds
    
class Command:
    def __init__(self):
#       self.data4_align_in_lines_by_sep  = ''
        self.cur_tab_id = None
        self.pre_tab_id = None
        
    def on_focus(self, ed_self):
        self.pre_tab_id = self.cur_tab_id
        self.cur_tab_id = ed_self.get_prop(app.PROP_TAB_ID)
        pass;                  #LOG and log('pre_tab_id,(cur_tab_id,cap)={}',(self.pre_tab_id,(self.cur_tab_id,ed.get_prop(app.PROP_TAB_TITLE))))
       
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
            # [('G'+str(i), list(zip(('|','V','P','F'), app.app_proc(app.PROC_GET_SPLIT, 'G'+str(i))))) for i in (1,2,3)]
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
            # 1P2VERT   0 G3 1 
            #                G2 
            #                2 
            # 1P2HORZ   0
            #           G3 
            #           1 G2 2 
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
#           and   grouping!=app.GROUPS_3PLUS):      id_splt = 'G1'
            and   grouping!=app.GROUPS_1P2VERT
            and   grouping!=app.GROUPS_1P2HORZ):    id_splt = 'G1'
            
            elif (what=='main' 
#           and   grouping==app.GROUPS_3PLUS):      id_splt = 'G3'
            and   grouping==app.GROUPS_1P2VERT):    id_splt = 'G3'

            elif (what=='main' 
            and   grouping==app.GROUPS_1P2HORZ):    id_splt = 'G3'

            #     what=='curr'
            elif cur_grp==0:
                if False:pass
                elif grouping==app.GROUPS_2HORZ:    id_splt = 'G1'  # w-self
                elif grouping==app.GROUPS_2VERT:    id_splt = 'G1'  # h-self
                elif grouping==app.GROUPS_3HORZ:    id_splt = 'G1'  # w-self
                elif grouping==app.GROUPS_3VERT:    id_splt = 'G1'  # h-self
#               elif grouping==app.GROUPS_3PLUS:    id_splt = 'G3'  # w-self
                elif grouping==app.GROUPS_1P2VERT:  id_splt = 'G3'  # w-self
                elif grouping==app.GROUPS_1P2HORZ:  id_splt = 'G3'  # h-self
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
#               elif grouping==app.GROUPS_3PLUS:    id_splt = 'G2'  # h-self
                elif grouping==app.GROUPS_1P2VERT:  id_splt = 'G2'  # h-self
                elif grouping==app.GROUPS_1P2HORZ:  id_splt = 'G2'  # w-self
                elif grouping==app.GROUPS_4HORZ:    id_splt = 'G2'  # w-self
                elif grouping==app.GROUPS_4VERT:    id_splt = 'G2'  # h-self
                elif grouping==app.GROUPS_4GRID:    id_splt ='-G1'  # w-left
                elif grouping==app.GROUPS_6GRID:    id_splt = 'G2'  # w-self

            elif cur_grp==2:
                if False:pass
                elif grouping==app.GROUPS_3HORZ:    id_splt ='-G2'  # w-left
                elif grouping==app.GROUPS_3VERT:    id_splt ='-G2'  # h-top
#               elif grouping==app.GROUPS_3PLUS:    id_splt ='-G2'  # h-top
                elif grouping==app.GROUPS_1P2VERT:  id_splt ='-G2'  # h-top
                elif grouping==app.GROUPS_1P2HORZ:  id_splt ='-G2'  # w-left
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

    def edit_strcomment_chars(self):
        lex     = ed.get_prop(app.PROP_LEXER_CARET)
        if not lex: return app.msg_status(NO_LEXER)
        def_lexs_json   = os.path.join(apx.get_def_setting_dir()         , 'default_lexers.json')
        usr_lexs_json   = os.path.join(app.app_path(app.APP_DIR_SETTINGS), 'user_lexers.json')
        def_lexs        = apx._json_loads(open(def_lexs_json).read())
        usr_lexs        = apx._json_loads(open(usr_lexs_json).read()) if os.path.exists(usr_lexs_json) else {"Comments":{}, "CommentsForLines":{}}
        pass;                  #LOG and log('usr_lexs={}',usr_lexs)
        only_ln         = False
        pair_df         = ['','']
        pair            = ['','']
        if False:pass
        elif lex in   def_lexs["Comments"]:
            pair_df = def_lexs["Comments"].get(lex)
        elif lex in   def_lexs["CommentsForLines"]:
            pair_df = def_lexs["CommentsForLines"].get(lex)
            only_ln = True
        if False:pass
        elif lex in   usr_lexs["Comments"]:
            pair    = usr_lexs["Comments"].get(lex)
        elif lex in   usr_lexs["CommentsForLines"]:
            pair    = usr_lexs["CommentsForLines"].get(lex)
            only_ln = True
        elif lex in   def_lexs["Comments"]:
            pair    = def_lexs["Comments"].get(lex)
        elif lex in   def_lexs["CommentsForLines"]:
            pair    = def_lexs["CommentsForLines"].get(lex)
            only_ln = True
        vals        = dict(stcs=pair[   0]
                          ,stdf=pair_df[0]
                          ,encs=pair[   1]
                          ,endf=pair_df[1]
                          ,full=only_ln   )
        while True:
            btn,vals,chds   = dlg_wrapper(f(_('Stream comment chars for lexer "{}"'), lex), GAP*3+100+165*2, GAP+105+GAP,     #NOTE: dlg-str-cmnt
                 [dict(           tp='lb'   ,t=GAP          ,l=GAP+100+GAP+165  ,w=165  ,cap=_('Default values')    ) #
                 ,dict(           tp='lb'   ,tid='stcs'     ,l=GAP              ,w=100  ,cap=_('&Start chars')      ) # &s
                 ,dict(cid='stcs',tp='ed'   ,t=GAP+20       ,l=GAP+100          ,w=165                              ) # 
                 ,dict(cid='stdf',tp='ed'   ,tid='stcs'     ,l=GAP+100+GAP+165  ,w=165  ,props='1,0,1'              ) #     ro,mono,border
                 ,dict(           tp='lb'   ,tid='encs'     ,l=GAP              ,w=100  ,cap=_('&Finish chars')     ) # &f
                 ,dict(cid='encs',tp='ed'   ,t=GAP+50       ,l=GAP+100          ,w=165                              ) # 
                 ,dict(cid='endf',tp='ed'   ,tid='encs'     ,l=GAP+100+GAP+165  ,w=165  ,props='1,0,1'              ) #     ro,mono,border
                 ,dict(cid='full',tp='ch'   ,t=GAP+80       ,l=GAP+100          ,w=165  ,cap=_('Only f&ull lines')  ) # &u
                 ,dict(cid='!'   ,tp='bt'   ,tid='full'     ,l=GAP+GAP+430-165  ,w=80   ,cap=_('Save'),props='1'    ) #     default
                 ,dict(cid='-'   ,tp='bt'   ,tid='full'     ,l=GAP+GAP+430-80   ,w=80   ,cap=_('Cancel')            )
                 ], vals, focus_cid='stcs')
            pass;              #LOG and log('vals={}',(vals))
            if btn is None or btn=='-': return None
            pair        = [vals['stcs'], vals['encs']]
            only_ln     = vals['full']
            # Checking
            if not pair[0] or not pair[1]:
                app.msg_box(USE_NOT_EMPTY, app.MB_OK)
                continue #while
            break #while 
           #while
           
        #Saving
        usr_lexs["Comments"         if only_ln else "CommentsForLines"].pop(lex, None)
        usr_lexs["CommentsForLines" if only_ln else "Comments"        ][lex] = pair
        open(usr_lexs_json, 'w').write(json.dumps(usr_lexs, indent=2))
        app.msg_status(f(_('File "{}" is updated'), usr_lexs_json))
       #def edit_strcomment_chars
    
    def rename_file(self):
        old_path= ed.get_filename()
        if not old_path:
            return ed.cmd(cmds.cmd_FileSaveAs)
        old_fn  = os.path.basename(old_path)
        old_stem= old_fn[: old_fn.rindex('.')]  if '.' in old_fn else old_fn
        old_ext = old_fn[1+old_fn.rindex('.'):] if '.' in old_fn else ''
        DLG_W,\
        DLG_H   = (300, 80)
        new_stem= old_stem
        new_ext = old_ext
        while True:
            btn,vals,chds   = dlg_wrapper(_('Rename file'), GAP+300+GAP,GAP+80+GAP,     #NOTE: dlg-rename
                 [dict(           tp='lb'   ,t=GAP          ,l=GAP          ,w=200      ,cap=_('Enter new file name:')  ) # &e
                 ,dict(cid='stem',tp='ed'   ,t=GAP+18       ,l=GAP          ,w=200+10                                   ) # 
                 ,dict(           tp='lb'   ,tid='stem'     ,l=GAP+200+12   ,w=8        ,cap='.'                        ) # &.
                 ,dict(cid='sext',tp='ed'   ,tid='stem'     ,l=GAP+200+20   ,w=80                                       )
                 ,dict(cid='!'   ,tp='bt'   ,t=GAP+80-28    ,l=GAP+300-170  ,w=80       ,cap=_('Save'),props='1'        ) #     default
                 ,dict(cid='-'   ,tp='bt'   ,t=GAP+80-28    ,l=GAP+300-80   ,w=80       ,cap=_('Close')                 )
                 ],    dict(stem=new_stem
                           ,sext=new_ext), focus_cid='stem')
            if btn is None or btn=='-': return None
            new_stem    = vals['stem']
            new_ext     = vals['sext']
            if new_stem==old_stem and new_ext==old_ext:
               return
            new_path    = os.path.dirname(old_path) + os.sep + new_stem + ('.'+new_ext if new_ext else '')
            if os.path.isdir(new_path):
                app.msg_box(f(_('There is directory with name:\n{}\n\nChoose another name.'), new_path), app.MB_OK)
                continue#while
            if os.path.isfile(new_path):
                if app.ID_NO==app.msg_box(_('File already exists.\nReplace?'), app.MB_YESNO):
                    continue#while
            break#while
           #while

        group       = ed.get_prop(app.PROP_INDEX_GROUP)
        tab_pos     = ed.get_prop(app.PROP_INDEX_TAB)
        crt         = ed.get_carets()[0]

        if ed.get_prop(app.PROP_MODIFIED):
            ans     = app.msg_box(_('Text modified.\nSave it?\n\nYes - Save and rename\nNo - Lost and rename\nCancel - Nothing'), app.MB_YESNOCANCEL)
            if ans==app.ID_CANCEL:  return
            if ans==app.ID_NO:
                ed.set_prop(app.PROP_MODIFIED, '0')     #? Changes lose!
            if ans==app.ID_YES:
                ed.save()
        os.replace(old_path, new_path)
        ed.cmd(cmds.cmd_FileClose)
        app.file_open(new_path, group)
        ed.set_prop(app.PROP_INDEX_TAB, str(tab_pos))
        ed.set_caret(*crt)
       #def rename_file
    
    def on_console_nav(self, ed_self, text):    return Nav_cmds.on_console_nav(ed_self, text)
    def _open_file_near(self, where='right'):   return Nav_cmds._open_file_near(where)
    def open_selected(self):                    return Nav_cmds.open_selected()
    def nav_by_console_err(self):               return Nav_cmds.nav_by_console_err()
    
    def tree_path_to_status(self):              return Tree_cmds.tree_path_to_status()
    def set_nearest_tree_node(self):            return Tree_cmds.set_nearest_tree_node()
    
    def add_indented_line_above(self):          return Insert_cmds.add_indented_line_above()
    def add_indented_line_below(self):          return Insert_cmds.add_indented_line_below()
    def paste_to_1st_col(self):                 return Insert_cmds.paste_to_1st_col()
    def paste_with_indent(self, where='above'): return Insert_cmds.paste_with_indent(where)
    def align_in_lines_by_sep(self):            return Insert_cmds.align_in_lines_by_sep()
    
    def find_cb_string_next(self):              return Find_repl_cmds.find_cb_by_cmd('dn')
    def find_cb_string_prev(self):              return Find_repl_cmds.find_cb_by_cmd('up')
    def replace_all_sel_to_cb(self):            return Find_repl_cmds.replace_all_sel_to_cb()
    
    def _activate_tab(self, group, tab_ind):    return Tabs_cmds._activate_tab(     group, tab_ind)
    def _activate_last_tab(self, group):        return Tabs_cmds._activate_last_tab(group)
    def _activate_near_tab(self, gap):          return Tabs_cmds._activate_near_tab(gap)
    def move_tab(self):                         return Tabs_cmds.move_tab()
    def close_tab_from_other_group(self
                        , what_grp='next'):     return Tabs_cmds.close_tab_from_other_group(what_grp)
    def go_back_tab(self):
        if  self.pre_tab_id \
        and self.pre_tab_id!=self.cur_tab_id:
            pre_ed  = apx.get_tab_by_id(self.pre_tab_id)
            if pre_ed:  pre_ed.focus()
       #def go_back_tab

    def jump_to_matching_bracket(self):     return Jumps_cmds.jump_to_matching_bracket()
    def scroll_to_center(self):             return Jumps_cmds.scroll_to_center()
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
[+][kv-kv][25nov15] Replace all as selected to cb-string: replace_all_sel_to_cb
[+][kv-kv][25nov15] Open selected file: open_selected
[+][kv-kv][25nov15] Catch on_console_nav
[+][kv-kv][26nov15] Scroll on_console_nav, Find*
[+][at-kv][09dec15] Refactor: find_pair
[+][kv-kv][15dec15] Find cb-string via cmd_FinderAction (for use next/prev after)
'''
