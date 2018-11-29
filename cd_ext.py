''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '1.5.27 2018-11-29'
ToDo: (see end of file)
'''

import  re, os, sys, json, collections, time, traceback
from    collections     import deque
from    fnmatch         import fnmatch

import  cudatext            as app
from    cudatext        import ed
from    cudatext_keys   import *
import  cudatext_cmd        as cmds
import  cudax_lib           as apx
from    cudax_lib       import log
try:
    from    .cd_plug_lib    import *
    # I18N
    _   = get_translation(__file__)
except:
    _   = lambda p:p

d       = dict
OrdDict = collections.OrderedDict
first_true  = lambda iterable, default=False, pred=None: next(filter(pred, iterable), default)  # 10.1.2. Itertools Recipes

FROM_API_VERSION    = '1.0.119'
FROM_API_VERSION    = '1.0.182'     # PROC_SPLITTER_GET/SET, LOG_CONSOLE_GET_MEMO_LINES
MIN_API_VER_4_REPL  = '1.0.169'
MIN_API_VER_4_REPL  = '1.0.187'     # LEXER_GET_PROP

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
NO_SPR_IN_LINES     = _("No separator '{}' in selected lines")
DONT_NEED_CHANGE    = _("Text change not needed")

pass;                           # Logging
pass;                           from pprint import pformat
pass;                           pfrm100=lambda d:pformat(d,width=100)
pass;                           LOG = (-2== 2)  # Do or dont logging.
pass;                           ##!! waits correction

c1      = chr(1)
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
        pass;                  #log('?',())
        path_l, gap = Tree_cmds._get_best_tree_path(ed.get_carets()[0][1])
        if not path_l:  return
#       ID_TREE = app.app_proc(app.PROC_SIDEPANEL_GET_CONTROL, 'Tree')
        ID_TREE = app.app_proc(app.PROC_SIDEPANEL_GET_CONTROL, 'Code tree')
        if not ID_TREE: return
        id_sel  = app.tree_proc(ID_TREE, app.TREE_ITEM_GET_SELECTED)
        id_need = path_l[-1][0]
        if id_need != id_sel:
            app.tree_proc(ID_TREE, app.TREE_ITEM_SELECT, id_need)
        path    = '['+ '] / ['.join([cap.rstrip(':')[:40] for (nid,cap) in path_l]) + ']'
#       path    =       ' // '.join([cap.rstrip(':')[:40] for (nid,cap) in path_l])
        return app.msg_status_alt(
            path if gap==0 else f('[{:+}] {}', -gap, path)
        , 10)
        
#       if gap==0:  return app.msg_status_alt(path, 10)
#       if gap==0:  return app.msg_status(    path)
#       app.msg_status_alt( f('[{:+}] {}', -gap, path), 10)
#       app.msg_status(     f('[{:+}] {}', -gap, path))
       #def tree_path_to_status
   
    @staticmethod
    def find_tree_node():
        HELP_C  = _(
            'Search starts on Enter.'
          '\r• A found node after current one will be selected.'
          '\r• All found nodes are remembered and dialog can jump over them by [Shift+]Enter or by menu commands.'
          '\r• If option "O" (wrapped search) is tuned on:'
          '\r    - Search continues from the start, when end of the tree is reached'
          '\r    - Jumps to previous/next nodes are looped too'
          '\r• Option ".*" (regular expression) allows to use Python reg.ex. See "docs.python.org/3/library/re.html".'
          '\r• Option "w" (whole words) is ignored if entered string contains not a word.'
          '\r• If option "Close on success" (in menu) is tuned on, dialog will close after successful search.'
          '\r• Option "Show full tree path" (in menu) shows in the statusbar the path of the found node (names of all parents).'
          '\r• Command "Restore initial selection" (in menu) restores only first of initial carets.'
        )
        ed_crts = ed.get_carets()           # Carets at start
        opts    = d(reex=False,case=False,word=False,wrap=False,hist=[],clos=False,fpth=False)
        opts.update(get_hist('tree.find_node', opts))
        # Scan Tree
        ID_TREE = app.app_proc(app.PROC_SIDEPANEL_GET_CONTROL, 'Code tree')
        if not ID_TREE: return app.msg_status(_('No CodeTree'))
        if not app.tree_proc(ID_TREE, app.TREE_ITEM_ENUM, 0):   # 0 is root
            ed.cmd(cmds.cmd_TreeUpdate)                         # Try to build tree
        tree_t  = []        # [{nid:ID, sub:[{nid:ID, sub:{}, cap:'smth', path:['rt','smth']},], cap:'rt', path:[]},]
        tree_p  = []        # [,(ID, 'smth',['rt','smth']),]
        def scan_tree(id_prnt, tree_nds, path_prnt):
            nonlocal tree_p
            kids            = app.tree_proc(ID_TREE, app.TREE_ITEM_ENUM, id_prnt)
            if kids is None:    return None
            for nid, cap in kids:
                path        = path_prnt + [cap]
                tree_p     += [(nid, cap, path)]
                sub         = scan_tree(nid, [], path)
#               tree_nds   += [d(nid=nid, cap=cap, path=path, sub=sub) if sub else d(id=nid, cap=cap, path=path)]
            return tree_nds
           #def scan_tree
        scan_tree(0, tree_t, [])    # 0 is root
        pass;                  #log('tree_t={}',pfrm100(tree_t))
        pass;                  #log('tree_p={}',pfrm100(tree_p))
        
        # How to select node
        def select_node(nid):
            app.tree_proc(ID_TREE, app.TREE_ITEM_SELECT, nid)
            c_min, r_min,   \
            c_max, r_max    = app.tree_proc(ID_TREE, app.TREE_ITEM_GET_RANGE, nid)
            ed.set_caret(c_min, r_min)
           #def select_node
        
        # Ask
        MAX_HIST= apx.get_opt('ui_max_history_edits', 20)
        stbr    = None
        status  = lambda msg:  app.statusbar_proc(stbr, app.STATUSBAR_SET_CELL_TEXT, tag=1, value=msg)
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
        ready_l = []            # [(nid,cap|path,ndn)]
        ready_p = -1            # pos in ready_l
        nfnd_st = lambda: status(_('No suitable nodes'))
        ready_st= lambda: status(f('{pos}/{all}:  {cap}', pos=1+ready_p, all=len(ready_l), cap=ready_l[ready_p][1]))
        ready_er= lambda: status(_('Error'))
        
        def do_attr(aid, ag, data=''):
            nonlocal prev_wt
            prev_wt = ''
            return d(fid='what')
        def do_menu(aid, ag, data=''):
            def wnen_menu(ag, tag):
                nonlocal opts, prev_wt
                if   tag in ('prev','next'):    return do_next(tag, ag)
                if   tag in ('fpth','clos'):    prev_wt = '';   opts[tag] = not opts[tag]
                elif tag=='help':               app.msg_box(HELP_C, app.MB_OK)
                elif tag=='rest':               ed.set_caret(*ed_crts[0]);      return None
                return []
               #def wnen_menu
            ag.show_menu(aid,
                [ d(tag='help'  ,cap=_('&Help...')                                      ,cmd=wnen_menu
                ),d(             cap='-'
                ),d(tag='prev'  ,cap=_('Find &previous')                                ,cmd=wnen_menu  ,key='Shift+Enter'
                ),d(tag='next'  ,cap=_('F&ind next')                                    ,cmd=wnen_menu  ,key='Enter'
                ),d(             cap='-'
                ),d(tag='fpth'  ,cap=_('Show full tree path')   ,ch=opts['fpth']        ,cmd=wnen_menu
                ),d(tag='clos'  ,cap=_('Close on success')      ,ch=opts['clos']        ,cmd=wnen_menu
                ),d(             cap='-'
                ),d(tag='rest'  ,cap=_('Restore initial selection and close dialog &=') ,cmd=wnen_menu  ,key='Shift+Esc'
                )]
            )
            return d(fid='what')
           #def do_menu
        def do_next(aid, ag, data=''):
            if not ready_l:         return d(fid='what')
            nonlocal ready_p
            ready_n = ready_p + (-1 if aid=='prev' else 1)
            ready_n = ready_n % len(ready_l) if opts['wrap'] else max(0, min(len(ready_l)-1, ready_n), 0)
            pass;              #log('ready_n,ready_p={}',(ready_n,ready_p))
            if ready_p == ready_n:  return d(fid='what')
            ready_p = ready_n
            ready_st()
            select_node(ready_l[ready_p][0])
            return d(fid='what')
           #def do_next
        def do_find(aid, ag, data=''):
            nonlocal opts, tree_p, prev_wt, ready_l, ready_p
            # What/how/where will search
            what        = ag.cval('what')
            if prev_wt==what and ready_l:
                return do_next('next', ag)
            prev_wt  = what
            pass;              #log('what={}',(what))
            if not what:
                ready_l, ready_p    = [], -1
                return d(fid='what')
            opts['hist']= add_to_hist(what, opts['hist'])
            opts.update(ag.cvals(['reex','case','word','wrap']))
            pass;              #log('opts={}',(opts))
            tree_sid    = app.tree_proc(ID_TREE, app.TREE_ITEM_GET_SELECTED)    # cur
            nodes       = tree_p                                                # To find from top
            if tree_sid and opts['clos']:                                       # To find from cur
                # Trick: [..,i,sid]+[j,..]   switch to   [j,..] or [j,..]+[..,i]  to search first after cur
                nids    = [nid for nid, cap, path in tree_p]
                pos     = nids.index(tree_sid)
                nodes   = tree_p[pos+1:] + (tree_p[:pos] if opts['wrap'] else [])
#               pass;          #log('nodes={}',pfrm100(nodes))
            # Search
            ready_l = []
            tree_ndn= -1
            try:
                pttn_r  = compile_pttn(what, opts['reex'], opts['case'], opts['word'])
            except:
                ready_er()
                return d(ctrls=[('what',d(items=opts['hist']))]
                        ,fid='what')
            for ndn, (nid, cap, path) in enumerate(nodes):
                if not pttn_r.search(cap):  continue
                if opts['clos']:
                    select_node(nid)
                    return None         # Close dlg
                ready_l+= [(nid, ' / '.join(path) if opts['fpth'] else cap, ndn)]
                tree_ndn= ndn if ndn==tree_sid else tree_ndn
            pass;              #log('ready_l={}',(ready_l))
            ready_p = -1    if not ready_l  else \
                      0     if not tree_sid else \
                      first_true(enumerate(ready_l), 0, (lambda n_nid_cap_ndn: n_nid_cap_ndn[1][2]>tree_ndn))[0]
            pass;              #log('ready_p={}',(ready_p))
            # Show results
            if ready_p!=-1:
                select_node(ready_l[ready_p][0])
                if opts['clos']:
                    return None         # Close dlg
                ready_st()
            else:
                nfnd_st()
            return d(ctrls=[('what',d(items=opts['hist']))]
                    ,fid='what')
           #def do_find
        def do_key_down(idd, idc, data=''):
            scam    = data if data else app.app_proc(app.PROC_GET_KEYSTATE, '')
            if 0:pass
            elif (scam,idc)==('s',VK_ENTER):        # Shift+Enter
                ag._update_on_call(do_next('prev', ag))
            elif (scam,idc)==('s',VK_ESCAPE):       # Shift+Esc
                ed.set_caret(*ed_crts[0])
                ag.hide()
            else: return
            return False
        ag      = DlgAgent(
            form    =dict(cap=_('Find tree node'), w=365, h=58, h_max=58
                         ,on_key_down=do_key_down
                         ,border=app.DBORDER_SIZE
                         ,resize=True)
        ,   ctrls   =[0
    ,('find',d(tp='bt'  ,t=0        ,l=-99      ,w=44   ,cap=''     ,sto=False  ,def_bt='1'             ,call=do_find           ))  # Enter
    ,('reex',d(tp='ch-b',tid='what' ,l=5+38*0   ,w=39   ,cap='.&*'  ,hint=_('Regular expression')       ,call=do_attr           ))  # &*
    ,('case',d(tp='ch-b',tid='what' ,l=5+38*1   ,w=39   ,cap='&aA'  ,hint=_('Case sensitive')           ,call=do_attr           ))  # &a
    ,('word',d(tp='ch-b',tid='what' ,l=5+38*2   ,w=39   ,cap='"&w"' ,hint=_('Whole words')              ,call=do_attr           ))  # &w
    ,('wrap',d(tp='ch-b',tid='what' ,l=5+38*3   ,w=39   ,cap='&O'   ,hint=_('Wrapped search')           ,call=do_attr           ))  # &/
    ,('what',d(tp='cb'  ,t  =5      ,l=5+38*4+5 ,w=155  ,items=opts['hist']                                             ,a='lR' ))  # 
    ,('menu',d(tp='bt'  ,tid='what' ,l=320      ,w=40   ,cap='&='                                       ,call=do_menu   ,a='LR' ))  # &=
    ,('stbr',d(tp='sb'              ,l=0        ,r=365                                   ,ali=ALI_BT                    ,a='lR' ))  # 
                    ][1:]
        ,   fid     ='what'
        ,   vals    = {k:opts[k] for k in ('reex','case','word','wrap')}
                              #,options={'gen_repro_to_file':'repro_dlg_find_tree_node.py'}
        )
        stbr    = app.dlg_proc(ag.id_dlg, app.DLG_CTL_HANDLE, name='stbr')
        app.statusbar_proc(stbr, app.STATUSBAR_ADD_CELL             , tag=1)
        app.statusbar_proc(stbr, app.STATUSBAR_SET_CELL_AUTOSTRETCH , tag=1, value=True)
        ag.show(lambda ag: set_hist('tree.find_node', upd_dict(opts, ag.cvals(['reex','case','word','wrap']))))
       #def find_tree_node
   
    @staticmethod
    def set_nearest_tree_node():
        path_l, gap = Tree_cmds._get_best_tree_path(ed.get_carets()[0][1])
        if not path_l:  return
        ID_TREE = app.app_proc(app.PROC_SIDEPANEL_GET_CONTROL, 'Code tree')
        if not ID_TREE: return
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
        ed.cmd(cmds.cmd_TreeUpdate)
        ID_TREE = app.app_proc(app.PROC_SIDEPANEL_GET_CONTROL, 'Code tree')
        INF     = 0xFFFFFFFF
        if not ID_TREE: return [], INF
        NO_ID   = -1
        def best_path(id_prnt, prnt_cap=''):
            rsp_l   = []
            kids    = app.tree_proc(ID_TREE, app.TREE_ITEM_ENUM, id_prnt)
            pass;              #LOG and log('>>id_prnt, prnt_cap, kids={}',(id_prnt, prnt_cap, len(kids) if kids else 0))
            if kids is None:
                pass;          #LOG and log('<<no kids',())
                return [], INF
            row_bfr, kid_bfr, cap_bfr = -INF, NO_ID, ''
            row_aft, kid_aft, cap_aft = +INF, NO_ID, ''
            for kid, cap in kids:
                pass;           LOG and log('kid, cap={}',(kid, cap))
                cMin, rMin, \
                cMax, rMax  = app.tree_proc(ID_TREE, app.TREE_ITEM_GET_SYNTAX_RANGE , kid) \
                                if app.app_api_version() < '1.0.226' else \
                              app.tree_proc(ID_TREE, app.TREE_ITEM_GET_RANGE        , kid)
                pass;          #LOG and log('? kid,cap, rMin,rMax,row={}',(kid,cap, rMin,rMax,row))
                if False:pass
                elif rMin<=row<=rMax:   # Cover!
                    sub_l, gap_sub  = best_path(kid, cap)
                    pass;      #LOG and log('? sub_l, gap_sub={}',(sub_l, gap_sub))
                    if gap_sub == 0:    # Sub-kid also covers
                        pass;  #LOG and log('+ sub_l={}',(sub_l))
                        rsp_l   = [(kid, cap)] + sub_l
                    else:               # The kid is best
                        pass;  #LOG and log('0 ',())
                        rsp_l   = [(kid, cap)]
                    pass;       LOG and log('<<! rsp_l={}',(rsp_l))
                    return rsp_l, 0
                elif row_bfr                  < rMax            < row:
                    row_bfr, kid_bfr, cap_bfr = rMax, kid, cap
                    pass;      #LOG and log('< row_bfr, kid_bfr, cap_bfr={}',(row_bfr, kid_bfr, cap_bfr))
                elif row_aft                  > rMin            > row:
                    row_aft, kid_aft, cap_aft = rMin, kid, cap
                    pass;      #LOG and log('> row_aft, kid_aft, cap_aft={}',(row_aft, kid_aft, cap_aft))
               #for kid
            pass;              #LOG and log('? row_bfr, kid_bfr, cap_bfr={}',(row_bfr, kid_bfr, cap_bfr))
            pass;              #LOG and log('? row_aft, kid_aft, cap_aft={}',(row_aft, kid_aft, cap_aft))
            pass;              #LOG and log('? abs(row_bfr-row), abs(row_aft-row)={}',(abs(row_bfr-row), abs(row_aft-row)))
            kid_x, cap_x, gap_x = (kid_bfr, cap_bfr, row_bfr-row) \
                                if abs(row_bfr-row) <= abs(row_aft-row) else \
                                  (kid_aft, cap_aft, row_aft-row)
            pass;              #LOG and log('kid_x, cap_x, gap_x={}',(kid_x, cap_x, gap_x))
            sub_l, gap_sub  = best_path(kid_x, cap_x)
            pass;              #LOG and log('? sub_l,gap_sub ?? gap_x={}',(sub_l, gap_sub, gap_x))
            if abs(gap_sub) <= abs(gap_x):  # Sub-kid better
                rsp_l  = [(kid_x, cap_x)] + sub_l
                pass;           LOG and log('<<sub bt: rsp_l, gap_sub={}',(rsp_l, gap_sub))
                return rsp_l, gap_sub
            # The kid is best
            rsp_l   = [(kid_x, cap_x)]
            pass;               LOG and log('<<bst: rsp_l, gap_x={}',(rsp_l, gap_x))
            return rsp_l, gap_x
           #def best_path
        lst, gap= best_path(0)
        pass;                   LOG and log('lst, gap={}',(lst, gap))
        return lst, gap
       #def _get_best_tree_path
   #class Tree_cmds

#############################################################
class Tabs_cmds:
    @staticmethod
    def _activate_tab(group, tab_ind):
        pass;                   LOG and log('group, tab_ind={}',(group, tab_ind))
        for h in app.ed_handles():
            edH = app.Editor(h)
            pass;               LOG and log('h.g h.t={}',(edH.get_prop(app.PROP_INDEX_GROUP),edH.get_prop(app.PROP_INDEX_TAB)))
            if ( group  ==edH.get_prop(app.PROP_INDEX_GROUP)
            and  tab_ind==edH.get_prop(app.PROP_INDEX_TAB)):
                pass;           LOG and log('found',())
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
class SCBs:
    @staticmethod
    def copy_term():
        """ Find and copy to CB word or 'smth'/"smth"/[smth] near/around caret.
            Parse only (in parse order)
                ·a|c·      abc|·   ·|abc        "word"-chars are \w             · is [^\w_]
                'abc'|·    ·|"abc"              any quotes from "" ''           · is [^\w_]
                [abc]|·    ·|(abc)              any brackets from [](){}<>      · is [^\w_'"]
        """
        term,(bgn,end) = SCBs._parseTerm(ed)
        pass;                  #LOG and log('term,(bgn,end)={}',(term,(bgn,end)))
        pass;                  #LOG and log('test={}',(ed.get_text_line(ed.get_carets()[0][1])[bgn:end]))
        if term:
            app.app_proc(app.PROC_SET_CLIP, term)
            app.msg_status(f(_('Copy {}'), repr(term[:50])))
       #def copy_term

    @staticmethod
    def replace_term():
        """ Find a word or 'smth'/"smth"/[smth] near/around caret 
                and replace with CB-clip.
            Parse only (in parse order)
                ·a|c·      abc|·   ·|abc        "word"-chars are \w             · is [^\w_]
                'abc'|·    ·|"abc"              any quotes from "" ''           · is [^\w_]
                [abc]|·    ·|(abc)              any brackets from [](){}<>      · is [^\w_'"]
        """
        clip    = app.app_proc(app.PROC_GET_CLIP, '')
        if not clip:    return app.msg_status(_('No clip'))
        term,(bgn,end) = SCBs._parseTerm(ed)
        pass;                  #LOG and log('term,(bgn,end)={}',(term,(bgn,end)))
        pass;                  #LOG and log('test={}',(ed.get_text_line(ed.get_carets()[0][1])[bgn:end]))
        if term:
            row = ed.get_carets()[0][1]
            line= ed.get_text_line(row)
            line= line[:bgn] + clip + line[end:]
            ed.set_text_line(row, line)
            app.msg_status(f(_('Replace {} with clip'), repr(term[:50])))
       #def replace_term

    lexer       = None
    wrdchs      = ''
    wrdcs_re    = None
    quotes      = ''
    brckts      = ''
    opn2cls     = {}
    cls2opn     = {}
    allspec     = ''
    notspec_re  = None
    signs       = ''
    signs_re    = None
    @staticmethod
    def _prep_static_data():
        lexer           = ed.get_prop(app.PROP_LEXER_FILE)
        if SCBs.lexer==lexer and SCBs.quotes: return
        SCBs.wrdchs     = apx.get_opt('word_chars', '') + '_'
        SCBs.wrdcs_re   = re.compile(r'^[\w'+re.escape(SCBs.wrdchs)+']+')
        SCBs.quotes     = apx.get_opt('cudaext_quotes', '"'+"'")
        SCBs.brckts     = apx.get_opt('cudaext_brackets', '[](){}<>')
        SCBs.opn2cls    = {SCBs.brckts[i  ]:SCBs.brckts[i+1] for i in range(0,len(SCBs.brckts),2)}
        SCBs.cls2opn    = {SCBs.brckts[i+1]:SCBs.brckts[i  ] for i in range(0,len(SCBs.brckts),2)}
        SCBs.allspec    = SCBs.wrdchs + SCBs.quotes + SCBs.brckts
        SCBs.notspec_re = re.compile(r'^[\W'+re.escape(SCBs.allspec)+']+')
        SCBs.signs      = apx.get_opt('cudaext_signs', r'!@#$%^&*-=+;:\|,./?`~')
        SCBs.signs_re   = re.compile(r'^['+re.escape(SCBs.signs)+']+')
       #def _prep_static_data

    @staticmethod
    def _parseTerm(ted=ed, ops={}):         #NOTE: _parseTerm
        """ Find _term_ around caret *into* current line.
            Parse only (in parse order)
                ·a|c·      abc|·   ·|abc        "word"-chars are \w             · is [^\w_]
                'abc'|·    ·|"abc"              any quotes from "" ''           · is [^\w_]
                [abc]|·    ·|(abc)              any brackets from [](){}<>      · is [^\w_'"]
            Params from def/user/lex
                word_chars          (no)        Append chars to \w
                cudaext_quotes      '"          Using quotes 
                cudaext_brackets    [](){}<>    Using brackets
            Params
                ted     (ed)
                ops     dict({})    
                    only_word:False             Detect only term as "word"
            Return      
                term, col_brn, col_end          term = line[col_bgn:col_end]
        """
        NONE    = None, (None, None)
        crts    = ted.get_carets()
        if len(crts)>1:
            app.msg_status(_("Command doesn't work with multi-carets"))
            return NONE
        (cCrt, rCrt
        ,cEnd, rEnd)= crts[0]
        if cEnd!=-1:
            app.msg_status(_('Command works when no selection'))
            return NONE
        SCBs._prep_static_data()
        word_b  = ops.get('only_word', False)
        
        line    = ted.get_text_line(rCrt)
        c_crt   = cCrt

        c_aft   = line[c_crt]   if c_crt<len(line) else ' '
        c_bfr   = line[c_crt-1] if c_crt>0         else ' '
        pass;                  #LOG and log('c_crt,(c_bfr,c_aft),line={}',(c_crt,(c_bfr,c_aft),line))
        if      word_b \
        and not (c_bfr.isalnum() or c_bfr in SCBs.wrdchs) \
        and not (c_aft.isalnum() or c_aft in SCBs.wrdchs) :
            pass;              #LOG and log('for word unk bfr+aft',())
            return NONE
        if not word_b \
        and not (c_bfr.isalnum() or c_bfr in SCBs.quotes or c_bfr in SCBs.brckts) \
        and not (c_aft.isalnum() or c_aft in SCBs.quotes or c_aft in SCBs.brckts) :
            pass;              #LOG and log('for expr unk bfr+aft',())
            return NONE
        
        # Detect word
        if      (c_bfr.isalnum() or c_bfr in SCBs.wrdchs) \
        or      (c_aft.isalnum() or c_aft in SCBs.wrdchs) :
            pass;              #LOG and log('?? for word',())
            tx_bfr  = line[:c_crt]
            tx_aft  = line[ c_crt:]
            pass;              #LOG and log('tx_bfr,tx_aft={}',(tx_bfr,tx_aft))
            gp_aft  = 0
            gp_bfr  = 0
            if (c_bfr.isalnum() or c_bfr in SCBs.wrdchs):   # abc|
                tx_bfr_r= ''.join(reversed(tx_bfr))
                gp_bfr  = len(SCBs.wrdcs_re.search(tx_bfr_r).group())
            if (c_aft.isalnum() or c_aft in SCBs.wrdchs):   # |abc
                gp_aft  = len(SCBs.wrdcs_re.search(tx_aft  ).group())
            pass;              #LOG and log('gp_bfr,gp_aft={}',(gp_bfr,gp_aft))
            return line[c_crt-gp_bfr:c_crt+gp_aft], (c_crt-gp_bfr, c_crt+gp_aft)
        assert not word_b

        find_prms = None
        rfind_prms= None
        gap_crt     = 0
        if False:pass
        # Detect qouted
        elif c_bfr in SCBs.quotes and line.count(c_bfr, c_crt)%2==0:    #   'abc'|
            rfind_prms  = c_bfr, 0, c_crt-2
            gap_crt     = 0
        elif c_bfr in SCBs.quotes and line.count(c_bfr, c_crt)%2==1:    #   '|abc'
            find_prms   = c_bfr, c_crt
            gap_crt     = -1
        elif c_aft in SCBs.quotes and line.count(c_aft, c_crt)%2==0:    #   |'abc'
            find_prms   = c_aft, c_crt+1
            gap_crt     = 0
        elif c_aft in SCBs.quotes and line.count(c_aft, c_crt)%2==1:    #   'abc|'
            rfind_prms  = c_aft, 0, c_crt-1
            gap_crt     = 1
        # Detect brackets
        elif c_bfr in SCBs.cls2opn:                                     #   [...]|
            rfind_prms  = SCBs.cls2opn[c_bfr], 0, c_crt-2
            gap_crt     = 0
        elif c_bfr in SCBs.opn2cls:                                     #   [|..]
            find_prms   = SCBs.opn2cls[c_bfr], c_crt
            gap_crt     = -1
        elif c_aft in SCBs.opn2cls:                                     #   |[...]
            find_prms   = SCBs.opn2cls[c_aft], c_crt+1
            gap_crt     = 0
        elif c_aft in SCBs.cls2opn:                                     #   [..|]
            rfind_prms  = SCBs.cls2opn[c_aft], 0, c_crt-1
            gap_crt     = 1
        pass;                  #LOG and log('(rfind_prms,find_prms),gap_crt={}',((rfind_prms,find_prms),gap_crt))
        if rfind_prms:
            trm_bgn = line.rfind(*rfind_prms)
            pass;              #LOG and log('trm_bgn={}',(trm_bgn))
            return line[trm_bgn:c_crt+gap_crt          ], (trm_bgn      , c_crt+gap_crt)  if -1!=trm_bgn else NONE
        if find_prms:
            trm_end = line.find(*find_prms)
            pass;              #LOG and log('trm_end={}',(trm_end))
            return line[        c_crt+gap_crt:trm_end+1], (c_crt+gap_crt, trm_end+1    )  if -1!=trm_end else NONE
        return NONE
        #def _parseTerm

    @staticmethod
    def expand_sel(copy=False):
        """ Expand current selection to the nearest usefull state:
                caret -> word -> phrase in brakets/quotes -> phrase with brakets/quotes -> ...
            Example. | caret, <...> selection
                fun('smt and oth', par)
                fun('smt an|d oth', par)
                fun('smt <and> oth', par)
                fun('smt< and >oth', par)
                fun('<smt and oth>', par)
                fun(<'smt and oth'>, par)
                fun(<'smt and oth', par>)
                fun<('smt and oth', par)>
                <fun('smt and oth', par)>
            Params
                copy    Copy new (only changed) selected text to clipboard
            Return  
                        Selection is changed
        """
        pass;                  #LOG and log('copy={}',(copy))
        crts    = ed.get_carets()
        if len(crts)>1:
            app.msg_status(_("Command doesn't work with multi-carets"))
            return False
        SCBs._prep_static_data()
        def get_char_before(col, row, dfval):
            """ Get first not EOL char """
            line    = ed.get_text_line(row)
            if col>0:           return line[col-1], col      -1, row
            return dfval, 0, row
#           while row>0:
#               row -= 1
#               line= ed.get_text_line(row)
#               if line:        return line[   -1], len(line)-1, row
            return dfval, -1, -1
        def get_char_after(col, row, dfval):
            """ Get first not EOL char """
            line    = ed.get_text_line(row)
            if col<len(line)-1: return line[col+1], col+1, row
            return dfval, len(line), row
#           while row<ed.get_line_count()-1:
#               row += 1
#               line= ed.get_text_line(row)
#               if line:        return line[    0], 0,     row
            return dfval, -1, -1
        
        (cCrt, rCrt
        ,cEnd, rEnd)    = crts[0]
        if -1==rEnd:
            cEnd, rEnd  = cCrt, rCrt
        def set_sel(cSelBgn, rSelBgn, cSelEnd, rSelEnd):
            if (rCrt, cCrt) >= (rEnd, cEnd):
                ed.set_caret(cSelEnd, rSelEnd, cSelBgn, rSelBgn)
            else:
                ed.set_caret(cSelBgn, rSelBgn, cSelEnd, rSelEnd)
            if copy:
                sSel    = ed.get_text_sel()
                app.app_proc(app.PROC_SET_CLIP, sSel)
                return True
        ((rSelB, cSelB)
        ,(rSelE, cSelE))= apx.minmax((rCrt, cCrt), (rEnd, cEnd))
        cSelE          -= 1                 ##??
#       sSel            = ed.get_text_sel()
        pass;                  #LOG and log('(rSelB, cSelB),(rSelE, cSelE),sSel={}',((rSelB, cSelB),(rSelE, cSelE),sSel[:50]))
        sBfr,cBfr,rBfr  = get_char_before(cSelB, rSelB, ' ')
        sAft,cAft,rAft  = get_char_after( cSelE, rSelE, ' ')
        pass;                  #LOG and log('(sBfr,rBfr,cBfr),(sAft,rAft,cAft)={}',((sBfr,rBfr,cBfr),(sAft,rAft,cAft)))
        
        # Try to expand from '|smth|' to |'smth'| or from (|smth|) to |(smth|)
        pass;                  #LOG and log('sBfr==sAft and sBfr in SCBs.quotes={}',(sBfr==sAft and sBfr in SCBs.quotes))
        pass;                  #LOG and log('sBfr==SCBs.cls2opn.get(sAft)={}',(sBfr==SCBs.cls2opn.get(sAft)))
        if  sBfr and sAft and \
        (   sBfr==sAft and sBfr in SCBs.quotes
        or  sBfr==SCBs.cls2opn.get(sAft) ):
            pass;              #LOG and log('|smth| --> |"smth"| or from (|smth|) to |(smth)|',())
            return      set_sel(cBfr, rBfr, cAft+1, rAft)
            

        # Try to expand from (|smth| to (|smth...|) or |smth|) to (|...smth|)
        if  sBfr in SCBs.opn2cls:
            c_opn,c_cls,\
            cAft,rAft   = fnd_mtch_char(ed, sBfr, SCBs.opn2cls[sBfr], ed.get_text_line(rBfr), cBfr+1, rBfr, to_end=True)
            pass;              #LOG and log('c_opn, c_cls, cAft, rAft={}',(c_opn, c_cls, cAft, rAft))
            if -1!=rAft:
                pass;          #LOG and log('(|smth| --> (|smth...|)',())   #)
                return  set_sel(cSelB, rSelB, cAft, rAft)
        if  sAft in SCBs.cls2opn:
            c_opn,c_cls,\
            cBfr,rBfr   = fnd_mtch_char(ed, sAft, SCBs.cls2opn[sAft], ed.get_text_line(rAft), cAft-1, rAft, to_end=False)
            pass;              #LOG and log('c_opn, c_cls, cBfr,rBfr={}',(c_opn, c_cls, cBfr,rBfr))
            if -1!=rBfr:
                pass;          #LOG and log('|smth|) --> (|...smth|)',())   #(
                return  set_sel(cBfr+1, rBfr, cSelE+1, rSelE)
        
        # Try to expand from |smth|( to |smth(...)| or )|smth| to |(...)smth|
        if  sBfr in SCBs.cls2opn:
            c_opn,c_cls,\
            cBfr,rBfr   = fnd_mtch_char(ed, sBfr, SCBs.cls2opn[sBfr], ed.get_text_line(rBfr), cBfr-1, rBfr, to_end=False)
            pass;              #LOG and log('c_opn, c_cls, cBfr,rBfr={}',(c_opn, c_cls, cBfr,rBfr))
            if -1!=rBfr:
                pass;          #LOG and log(')|smth| --> |(...)smth|',())   #)
                return  set_sel(cBfr, rBfr, cSelE+1, rSelE)
        if  sAft in SCBs.opn2cls:
            c_opn,c_cls,\
            cAft,rAft   = fnd_mtch_char(ed, sAft, SCBs.opn2cls[sAft], ed.get_text_line(rAft), cAft+1, rAft, to_end=True)
            pass;              #LOG and log('c_opn, c_cls, cAft, rAft={}',(c_opn, c_cls, cAft, rAft))
            if -1!=rBfr:
                pass;          #LOG and log('|smth|( --> |smth(...)|',())   #(
                return  set_sel(cSelB, rSelB, cAft+1, rAft)
        
        # Try to expand from "|smth| smth" to "|smth smth|"
        if  sBfr in SCBs.quotes:
            line    = ed.get_text_line(rSelB)
            cNewE   = line.find(sBfr, cSelE+1)
            if -1!=cNewE:
                pass;          #LOG and log('"|smth| smth" --> "|smth smth|"',())
                return  set_sel(cSelB, rSelB, cNewE, rSelB)
        if  sAft in SCBs.quotes:
            line    = ed.get_text_line(rSelE)
            cNewB   = line.rfind(sAft, 0, cSelB)
            if -1!=cNewB:
                pass;          #LOG and log('"smth |smth|" --> "|smth smth|"',())
                return  set_sel(cNewB+1, rSelB, cSelB, rSelB)
        
        # Try to expand from |smth| to |ABCsmthXYX|
        sBfrTxR = ''
        nBfrGap = 0
        nAftGap = 0
        if  sBfr in SCBs.wrdchs or sBfr.isalnum() \
        or  sAft in SCBs.wrdchs or sAft.isalnum():
            if  sBfr in SCBs.wrdchs or sBfr.isalnum():
                sBfrLn  = ed.get_text_line(rBfr)
                sBfrTx  = sBfrLn[:cBfr]
                sBfrTxR = ''.join(reversed(sBfrTx)) if not sBfrTxR else sBfrTxR
                oBfrMch = SCBs.wrdcs_re.search(sBfrTxR)
                nBfrGap = len(oBfrMch.group()) if oBfrMch else 0
                pass;          #LOG and log('nBfrGap={}',(nBfrGap))
            else:
                nBfrGap = -1
            if  sAft in SCBs.wrdchs or sAft.isalnum():
                sAftLn  = ed.get_text_line(rAft)
                sAftTx  = sAftLn[cAft:]
                oAftMch = SCBs.wrdcs_re.search(sAftTx)
                nAftGap = len(oAftMch.group()) if oAftMch else 0
                pass;          #LOG and log('nAftGap={}',(nAftGap))
            pass;              #LOG and log('|smth| to |ABCsmthXYX|',())
            return      set_sel(cBfr-nBfrGap, rBfr, cAft+nAftGap, rAft)
        
        # Try to expand from |smth| to |.smth,|
        nBfrGap = 0
        nAftGap = 0
        if      sBfr in SCBs.signs\
        or      sAft in SCBs.signs :   #NOTE: do
            if  sBfr in SCBs.signs:
                sBfrLn  = ed.get_text_line(rBfr)
                sBfrTx  = sBfrLn[:cBfr]
                sBfrTxR = ''.join(reversed(sBfrTx)) if not sBfrTxR else sBfrTxR
                oBfrMch = SCBs.signs_re.search(sBfrTxR)
                nBfrGap = len(oBfrMch.group()) if oBfrMch else 0
                pass;          #LOG and log('nBfrGap={}',(nBfrGap))
            else:
                nBfrGap = -1
            if  sAft in SCBs.signs:
                sAftLn  = ed.get_text_line(rAft)
                sAftTx  = sAftLn[cAft:]
                oAftMch = SCBs.signs_re.search(sAftTx)
                nAftGap = len(oAftMch.group()) if oAftMch else 0
                pass;          #LOG and log('nAftGap={}',(nAftGap))
            pass;              #LOG and log('|smth| to |.smth,|',())
            return      set_sel(cBfr-nBfrGap, rBfr, cAft+nAftGap, rAft)

        # Try to expand from |smth| to |·smth·|
        assert not sBfr.isalnum() and not sAft.isalnum()
        nBfrGap = 0
        nAftGap = 0
        if      sBfr not in SCBs.allspec \
        or      sAft not in SCBs.allspec :
            if  sBfr not in SCBs.allspec:
                sBfrLn  = ed.get_text_line(rBfr)
                sBfrTx  = sBfrLn[:cBfr]
                sBfrTxR = ''.join(reversed(sBfrTx)) if not sBfrTxR else sBfrTxR
                oBfrMch = SCBs.notspec_re.search(sBfrTxR)
                nBfrGap = len(oBfrMch.group()) if oBfrMch else 0
                pass;          #LOG and log('nBfrGap={}',(nBfrGap))
            else:
                nBfrGap = -1
            if  sAft not in SCBs.allspec:
                sAftLn  = ed.get_text_line(rAft)
                sAftTx  = sAftLn[cAft:]
                oAftMch = SCBs.notspec_re.search(sAftTx)
                nAftGap = len(oAftMch.group()) if oAftMch else 0
                pass;          #LOG and log('nAftGap={}',(nAftGap))
            pass;              #LOG and log('|smth| to |·smth·|',())
            return      set_sel(cBfr-nBfrGap, rBfr, cAft+nAftGap, rAft)
        return False
       #def expand_sel
#  #class SCBs

#############################################################
class Jumps_cmds:
    @staticmethod
    def scroll_to(place):
       #wraped      = apx.get_opt('wrap_mode', False, apx.CONFIG_LEV_FILE)
       #last_on_top = apx.get_opt('show_last_line_on_top', False)
        if place in ('cen', 'top', 'bot'):
            txt_lines   = ed.get_line_count()
            old_top_line= ed.get_prop(app.PROP_LINE_TOP) if app.app_api_version()>='1.0.126' else ed.get_top()
            scr_lines   = ed.get_prop(app.PROP_VISIBLE_LINES)
            crt_line    = ed.get_carets()[0][1]
            vert_indent = apx.get_opt('cuda_ext_vert_indent', 0)
#           vert_indent = abs(apx.get_opt('find_indent_vert', 0))
        
            new_top_line= old_top_line
            if False:pass
            elif place=='cen':
                new_top_line= crt_line - int(scr_lines/2)
            elif place=='top':
                new_top_line= crt_line              - vert_indent
            elif place=='bot':
                new_top_line= crt_line - scr_lines  + vert_indent+1
            new_top_line= max(new_top_line, 0)
            new_top_line= min(new_top_line, txt_lines-1)
            pass;              #LOG and log('cur, old, new, scr, ind={}',(crt_line, old_top_line, new_top_line, scr_lines, vert_indent))
        
            if new_top_line!=old_top_line:
                if app.app_api_version()>='1.0.126':
                    ed.set_prop(app.PROP_LINE_TOP, str(new_top_line))
                else: # old
                    ed.set_top(new_top_line)

        if place in ('lf', 'rt') and 0==apx.get_opt('wrap_mode', 0):    # 0: off 
            free_crt    = apx.get_opt('caret_after_end', False)
            move_crt    = apx.get_opt('cuda_ext_horz_scroll_move_caret', False)
            shift       = apx.get_opt('cuda_ext_horz_scroll_size', 30)
            old_lf_col  = ed.get_prop(app.PROP_COLUMN_LEFT)
            
            new_lf_col  = old_lf_col + (-shift if place=='lf' else shift)
            new_lf_col  = max(new_lf_col, 0)
            pass;              #LOG and log('cols,old_l,new_l={}',(old_lf_col,new_lf_col))
            if new_lf_col==old_lf_col:                          return # Good state
            ed.set_prop(app.PROP_COLUMN_LEFT, str(new_lf_col))
            
            if not (free_crt and move_crt):                     return # No need opts
            # Move caret if it isnot shown
            crts        = ed.get_carets()
            if len(crts)>1:                                     return # M-carets
            if crts[0][2]!=-1:                                  return # With sel
            old_crt_pos,y   = crts[0][0], crts[0][1]
            old_crt_col,y   = ed.convert(app.CONVERT_CHAR_TO_COL, old_crt_pos, y)
            scr_cols        = ed.get_prop(app.PROP_VISIBLE_COLUMNS)
            if new_lf_col<=old_crt_col<(new_lf_col+scr_cols):   return # Visible
            new_crt_col     = new_lf_col + (old_crt_col-old_lf_col)
            new_crt_col     = min(max(new_crt_col, 0), new_lf_col + scr_cols)
            new_crt_pos,y   = ed.convert(app.CONVERT_COL_TO_CHAR, new_crt_col, y)
            pass;              #LOG and log('old_p,old_c,new_c,new_p={}',(old_crt_pos,old_crt_col,new_crt_col,new_crt_pos))
            ed.set_caret(new_crt_pos,y)
       #def scroll_to

    @staticmethod
    def jump_to_matching_bracket():
        ''' Jump single (only!) caret to matching bracket.
            Pairs: [] {} () <> «»
        '''
        pass;                      #LOG and log('')
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
        (cCrt, rCrt, cEnd, rEnd)    = crts[0]
        if cEnd!=-1:
            return app.msg_status(ONLY_FOR_NO_SEL.format(_('Command')))

        (c_opn, c_cls
        ,col, row)  = find_matching_char(ed, cCrt, rCrt)

        if c_opn!='' and -1!=col:
            pass;                  #LOG and log('set_caret(col, row)={}', (col, row))
            ed.set_caret(col, row)
        else:
            return app.msg_status(NO_PAIR_BRACKET.format(c_opn))
       #def jump_to_matching_bracket

    @staticmethod
    def jump_to_status_line(status, nx_pr, bgn_end):
        pass;                  #LOG and log('status, nx_pr, bgn_end={}',(status, nx_pr, bgn_end))
        trg_sts = [app.LINESTATE_SAVED  ]   if status=='svd' else \
                  [app.LINESTATE_CHANGED
                  ,app.LINESTATE_ADDED  ]   if status=='mod' else \
                  [app.LINESTATE_CHANGED
                  ,app.LINESTATE_SAVED
                  ,app.LINESTATE_ADDED  ]   if status=='wrk' else \
                  [app.LINESTATE_NORMAL ]
        step    = (-1 if nx_pr=='prev' else 1)
        fini_r  = ( 0 if nx_pr=='prev' else ed.get_line_count()-1)
        init_r  = ed.get_carets()[0][1]                             # Start from upper caret (not selection)
        init_st = ed.get_prop(app.PROP_LINE_STATE, init_r)          # Start status
        pass;                  #LOG and log('step,init_r,fini_r,trg_sts={}',(step,init_r,fini_r,trg_sts))
        
        trgt_r  = -1
        state   = 'to-free' if init_st in trg_sts else 'to-trgt'
        test_r  = init_r
        while True:
            test_r += step
            if test_r==fini_r: break#while
            test_st = ed.get_prop(app.PROP_LINE_STATE, test_r)
            pass;              #LOG and log('state,test_r,test_st={}',(state,test_r,test_st))
            if False:pass
            elif state == 'to-free' and test_st     in trg_sts:     #   in init wrk fragment
                pass
            elif state == 'to-free' and test_st not in trg_sts:     # exit init wrk fragment
                state   = 'to-trgt'
            elif state == 'to-trgt' and test_st not in trg_sts:     #   in free space
                state   = 'to-trgt'
            elif state == 'to-trgt' and test_st     in trg_sts:     # found
                trgt_r  = test_r
                if nx_pr=='next' and bgn_end=='bgn' or \
                   nx_pr=='prev' and bgn_end=='end': break#while    # true side of fragment
                state   = 'to-side'
            elif state == 'to-side' and test_st     in trg_sts:     #   in trgt fragment
                trgt_r  = test_r
            elif state == 'to-side' and test_st not in trg_sts:     # exit trgt fragment
                break#while
        
        if -1==trgt_r:  return app.msg_status(_("Not found lines by status"))
        ed.set_caret(0, trgt_r)
       #def jump_to_status_line
       
    @staticmethod
    def jump_to_line_by_cb():
        clip    = app.app_proc(app.PROC_GET_CLIP, '')
        row = -1
        try:    row = int(clip)-1
        except: return  app.msg_status(_("No line number in clipboard"))
        if not (0 <= row < ed.get_line_count()):
            return      app.msg_status(f(_("No line #{}"), row))
        ed.set_caret(0, row)
       #def jump_to_line_by_cb
       
    @staticmethod
    def jump_ccsc(drct='l', sel=False):
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
        core_cmds   = { ('r', False): cmds.cCommand_GotoWordNext
                      , ('l', False): cmds.cCommand_GotoWordPrev
                      , ('r', True ): cmds.cCommand_GotoWordNext_Sel
                      , ('l', True ): cmds.cCommand_GotoWordPrev_Sel
                      }
        (cCrt, rCrt, cEnd, rEnd)    = crts[0]
        line        = ed.get_text_line(rCrt)
        use_core    = ( drct=='l' and cCrt==0
                    or  drct=='l' and not re.search(r'\w', line[cCrt-1])
                    or  drct=='r' and cCrt>=len(line)
                    or  drct=='r' and not re.search(r'\w', line[cCrt])
                      )
        if use_core:    return ed.cmd(core_cmds[drct, sel])
        
        # Extract tail of word
        tail    = line[cCrt:] \
                    if drct=='r' else \
                  ''.join(reversed(line[:cCrt]))
        pass;                  #LOG and log('tail={}',(tail))
        tail    = re.search(r'\w+', tail).group()
        pass;                  #LOG and log('tail={}',(tail))
        
        # Scan to nearest aCamelCase or "_" in snake_case_case test___test___dd ddTest____DD__DDddd_test
        gap     = 0
        for pos, ch in enumerate(tail):
            if pos>0 and ch!='_' and ch==ch.upper():
                # Skip first and stop at next Camel
                gap = pos + (1 if drct=='l' else 0)     # For backward stop after C, for forward - before
                break
            if drct=='r' and ch=='_' and (pos+1)<len(tail) and tail[pos+1]!='_':
                # For forward stop after _
                gap = pos+1
                break
            if drct=='l' and ch!='_' and (pos+1)<len(tail) and tail[pos+1]=='_':
                # For backward stop before _
                gap = pos+1
                break
        pass;                  #LOG and log('gap={}',(gap))
        if gap==0:    return ed.cmd(core_cmds[drct, sel])
        gap     = gap if drct=='r' else -gap
        
        # Jump
        if not sel:
            ed.set_caret(cCrt + gap, rCrt)
        else:
            cEnd, rEnd  = (cCrt, rCrt) if cEnd==-1 else (cEnd, rEnd)
            ed.set_caret(cCrt + gap, rCrt, cEnd, rEnd)
       #def jump_ccsc
 
    @staticmethod
    def jump_staple(what):
        """ Move a caret along the nearest left staple """ 
        crts    = ed.get_carets()
        if len(crts)>1:     return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
        (cCrt, rCrt, cEnd, rEnd)    = crts[0]
        if cEnd!=-1:        return app.msg_status(ONLY_FOR_NO_SEL.format(_('Command')))
            
        folds   = ed.folding(app.FOLDING_GET_LIST) \
                    if app.app_api_version() < '1.0.265' else \
                  ed.folding(app.FOLDING_GET_LIST_FILTERED, item_y=rCrt, item_y2=rCrt)
        if not folds:       return app.msg_status(_('No staple to jump'))
        crt_r, crt_x, crt_c = rCrt, cCrt, ed.convert(app.CONVERT_CHAR_TO_COL, cCrt, rCrt)[0]
        pass;                  #log('what, crt_r, crt_x, crt_c={}', (what,crt_r, crt_x, crt_c))
        pass;                  #log('folds={}', (folds))
        folds   = [(y, y2, x) for (y, y2, x, staple, folded) 
                    in folds 
                    if  staple and not folded
                    and y<=crt_r<=y2
                  ]
        pass;                  #log('folds={}', (folds))
        if not folds:       return app.msg_status(_('No staple to jump'))
        best_yyс= None
        for y,y2,stp_x in folds:
            if stp_x==0:
                line_y  = ed.get_text_line(y)
                stp_x   = len(line_y) - len(line_y.lstrip())                # Count of start blanks
            stp_c       = ed.convert(app.CONVERT_CHAR_TO_COL, stp_x, y)[0]  # Column of staple
            best_yyс= (y,y2,stp_c) \
                        if stp_c <= crt_c and (not best_yyс or stp_c > best_yyс[2]) else \
                      best_yyс
            pass;              #log('y,y2,stp_x,stp_c,best_yyс={}', ((y,y2),(stp_x,stp_c),best_yyс))
        if not best_yyс:    return app.msg_status(_('No staple to jump'))
        new_r   = best_yyс[0 if what=='bgn' else 1]
        if new_r==crt_r:    return
        new_x   = ed.convert(app.CONVERT_COL_TO_CHAR, crt_c, new_r)[0]
        pass;                  #log('new_x, new_r={}', (new_x, new_r))
        ed.set_caret(new_x, new_r)
       #def jump_staple
 
    @staticmethod
    def dlg_bms_in_tab():
        bm_lns  = ed.bookmark(app.BOOKMARK_GET_LIST, 0)
        if not bm_lns:  return app.msg_status(_('No bookmarks'))
        tab_sps = ' '*ed.get_prop(app.PROP_TAB_SIZE)
        bms     = [ (line_num                                               # line number
                    ,ed.get_text_line(line_num).replace('\t', tab_sps)      # line string
                    ,ed.bookmark(app.BOOKMARK_GET_PROP, line_num)['kind']   # kind of bm
                    )   for line_num in bm_lns]
        pass;                  #LOG and log('bms=¶{}',pf(bms))
        rCrt    = ed.get_carets()[0][1]
        near    = min([(abs(line_n-rCrt), ind)
                        for ind, (line_n, line_s, bm_kind) in enumerate(bms)])[1]
        ans = app.dlg_menu(app.MENU_LIST, '\n'.join([
                f('{}\t{}{}'
                 , line_s
                 , f('[{}] ', bm_kind-1) if bm_kind!=1 else ''
                 , 1+line_n
                 ) for line_n, line_s, bm_kind in bms
                ]), near)
        if ans is None: return
        line_n, line_s, bm_kind    = bms[ans]
        ed.set_caret(0, line_n)
        if not (ed.get_prop(app.PROP_LINE_TOP) <= line_n <= ed.get_prop(app.PROP_LINE_BOTTOM)):
            ed.set_prop(app.PROP_LINE_TOP, str(max(0, line_n - max(5, apx.get_opt('find_indent_vert')))))
       #def dlg_bms_in_tab

    @staticmethod
    def dlg_bms_in_tabs(what='a'):
        pass;                  #return log('ok',())
        tnmd    = apx.get_opt('ui_tab_numbers', False)
        tbms    = []
        for h_tab in app.ed_handles():
            ted     = app.Editor(h_tab)
            bm_lns  = ted.bookmark(app.BOOKMARK_GET_LIST, 0)
            if not bm_lns:  continue
            tab_grp = ted.get_prop(app.PROP_INDEX_GROUP)
            tab_num = ted.get_prop(app.PROP_INDEX_TAB)
            tab_cap = ted.get_prop(app.PROP_TAB_TITLE)
            tab_id  = ted.get_prop(app.PROP_TAB_ID)
            tab_info= tab_cap \
                        if what=='a' else \
                      (f('(g{},t{}) ', 1+tab_grp, 1+tab_num) if tnmd else '') + tab_cap
            tab_id  = ted.get_prop(app.PROP_TAB_ID)
            tab_sps = ' '*ed.get_prop(app.PROP_TAB_SIZE)
            tbms   += [ (line_num                                               # line number
                        ,ted.get_text_line(line_num).replace('\t', tab_sps)     # line string
                        ,ted.bookmark(app.BOOKMARK_GET_PROP, line_num)['kind']  # kind of bm
                        ,tab_info                                               # src tab '(group:num) title'
                        ,tab_id                                                 # src tab ID
                        )   for line_num in bm_lns
                            if what=='a' or 1<ted.bookmark(app.BOOKMARK_GET_PROP, line_num)['kind']<10
                      ]
           #for h_tab
        if not tbms:    return app.msg_status(_('No numbered bookmarks in tabs') if what=='n' else _('No bookmarks in tabs'))
        tid     = ed.get_prop(app.PROP_TAB_ID)
        rCrt    = ed.get_carets()[0][1]
        near    = min([(abs(line_n-rCrt) if tid==tab_id else 0xFFFFFF, ind)
                    for ind, (line_n, line_s, bm_kind, tab_info, tab_id) in enumerate(tbms)])[1]
        ans     = app.dlg_menu(app.MENU_LIST, '\n'.join([
                        f('{}\t{}:{}{}'
                         , line_s
                         , tab_info
                         , f('[{}]', bm_kind-1) if bm_kind!=1 else ''
                         , 1+line_n
                         ) for line_n, line_s, bm_kind, tab_info, tab_id in tbms
                    ]), near) \
                                if what=='a' else \
                  app.dlg_menu(app.MENU_LIST_ALT, '\n'.join([
                        f('{}: {} {}\t{}'
                         , tab_info
                         , f('[{}] ', bm_kind-1) if bm_kind!=1 else ''
                         , 1+line_n
                         , line_s
                         ) for line_n, line_s, bm_kind, tab_info, tab_id in tbms
                    ]), near)
        if ans is None: return
        line_n, line_s, bm_kind, tab_info, tab_id    = tbms[ans]
        ted     = apx.get_tab_by_id(tab_id)
        ted.focus()
        ed.set_caret(0, line_n)
        if not (ed.get_prop(app.PROP_LINE_TOP) <= line_n <= ed.get_prop(app.PROP_LINE_BOTTOM)):
            ed.set_prop(app.PROP_LINE_TOP, str(max(0, line_n - max(5, apx.get_opt('find_indent_vert')))))
       #def dlg_bms_in_tabs

   #class Jumps_cmds

class Prgph_cmds:

    @staticmethod
    def go_prgph(what):
        """ Param 
                what    'bgn' - go to begin of current prph
                        'end' - go to end   of current prph
                        'nxt' - go to begin of next    prph
                        'prv' - go to begin of prev    prph
        """
        pass;                  #LOG and log('what={}',(what))
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
        (cCrt, rCrt, cEnd, rEnd)    = crts[0]
        cu_row  = rCrt
        
        cu_line = ed.get_text_line(cu_row)
        if ''==cu_line.strip() and what in ('bgn', 'end'):  return
        
        cu_skip = False
        if what=='end' and cu_row+1<ed.get_line_count():
            # Skip cu-prph if caret "at end" and cmd "go end"
            cu_skip = ''==ed.get_text_line(cu_row+1).strip() and \
                      cCrt==len(cu_line)
        if what=='bgn' and cu_row-1>=0:
            # Skip cu-prph if caret "at bgn" and cmd "go bgn"
            cu_skip = ''==ed.get_text_line(cu_row-1).strip() and \
                      cCrt<=len(cu_line)-len(cu_line.lstrip())
        
        if what in ('nxt', 'prv') or cu_skip:
            # Search row in other prph
            step    = 1 if what in ('nxt','end') else -1
            stop    =-1 if what in ('prv','bgn') else ed.get_line_count()
            aim     = 'skip-prph'
            for test_row in range(cu_row+step, stop, step):
                test_line   = ed.get_text_line(test_row)
                empty       = ''==test_line.strip()
                if False:pass
                elif aim=='skip-prph' and not empty:
                    pass
                elif aim=='skip-prph' and     empty:
                    aim = 'skip-free'
                elif aim=='skip-free' and     empty:
                    pass
                elif aim=='skip-free' and not empty:
                    aim = 'found'
                    break#for
               #for test_row
            if aim!='found':    return
            what    = 'bgn' if what in ('nxt', 'prv') else what
            cu_row  = test_row
            
        # Search need row in curr prph
        nd_row  = cu_row
        step    =-1 if what=='bgn' else 1
        stop    =-1 if what=='bgn' else ed.get_line_count()
        pass;                  #LOG and log('cu_row,step,stop={}',(cu_row,step,stop))
        for test_row in range(cu_row+step, stop, step):
            if ''==ed.get_text_line(test_row).strip():
                break#for
            nd_row  = test_row
           #for test_row
           
        # Set caret
        nd_text = ed.get_text_line(nd_row)
        nd_col  = len(nd_text) - len(nd_text.lstrip()) \
                    if what=='bgn' else \
                  len(nd_text)
        ed.set_caret(nd_col, nd_row)
       #def go_prgph

    @staticmethod
    def align_prgph(how):
        """ Align words in selected paragraphs
            Param 
                how     'l' - left
                        'r' - right
                        'c' - center
                        'f' - full
                        '?' - edit params
        """
        pass;                  #LOG and log('how={}',(how))
        df_mrg  = apx.get_opt('margin', 80)
        if how=='?':
            df_m    = str(df_mrg)
            ans     = app.dlg_input_ex(3, _('Align paragraphs - options (default values)')
                , _('Paragraph right margin ('+df_m+')'), str(apx.get_opt('margin_right'    , df_mrg))
                , _('Indent of first line (0)')         , str(apx.get_opt('margin_left_1'   , 0))
                , _('Indent of other lines (0)')        , str(apx.get_opt('margin_left'     , 0))
                )
            if ans:
                apx.set_opt('margin_right'  , int(ans[0]) if ans[0].isdigit() else df_mrg)
                apx.set_opt('margin_left_1' , int(ans[1]) if ans[1].isdigit() else 0)
                apx.set_opt('margin_left'   , int(ans[2]) if ans[2].isdigit() else 0)
            return
        
        if 0==apx.get_opt('margin_right', 0):
            Prgph_cmds.align_prgph('?')
            if 0==apx.get_opt('margin_right', 0):
                return
            
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))

        max_col = apx.get_opt('margin_right'    , df_mrg)
        indent  = apx.get_opt('margin_left'     , 0)
        indent1 = apx.get_opt('margin_left_1'   , 0)
        (cCrt, rCrt, cEnd, rEnd)    = crts[0]
        min_row,\
        max_row = apx.minmax(rCrt, rEnd) if -1!=rEnd else (rCrt, rCrt)

        prphs   = Prgph_cmds._detect_prphs(min_row, max_row)
        pass;                  #LOG and log('prphs={}',(prphs))
        pass;                  #return
        
        for (prph_bgn_r, prphs_end_r) in reversed(prphs):
            prph_text   = ' '.join([ed.get_text_line(r)
                                    for r in range(prph_bgn_r, prphs_end_r+1)])     # join
            pass;              #LOG and log('prph_text={}',(prph_text))
            prph_text   = re.sub(r'(\s)\s+', r'\1', prph_text)                      # reduce
            pass;              #LOG and log('prph_text={}',(prph_text))
            prph_lines  = Prgph_cmds._form_prph(prph_text, how, max_col, indent, indent1)   # split and align
            pass;              #LOG and log('prph_lines={}',('\n'+'\n'.join(prph_lines)))
            ed.replace_lines(prph_bgn_r, prphs_end_r, prph_lines)
       #def align_prgph
       
    def _form_prph(text, how, max_col, indent=0, indent1=0):
        words   = [m.group() for m in re.finditer(r'\S+', text)]
#       words   = [m.group() for m in re.finditer(r'\b\S+\b', text)]
        if not words:
            return [text]
        
        width1  = max_col - indent1
        width   = max_col - indent
        pass;                  #LOG and log('width1,width={}',(width1,width))
        line_ws = []
        line_ns = []
        # Draft split
        line_n  = 0
        line    = []
        for word in words:
            if not line:
                # First word in line has any length
                line_n  = len(word)
                line    = [   word]
                continue
            if  line_n +    len(word) < (width if line_ws else width1):
                line_n += 1+len(word)
                line   += [' ', word]
            else:
                line_ws+= [line]
                line_ns+= [line_n]
                line_n  = len(word)
                line    = [   word]
           #for word
        if line:
            # tail
            line_ws+= [line]
            line_ns+= [line_n]
        pass;                  #LOG and log('line_ws={}',(line_ws))
        pass;                  #LOG and log('line_ns={}',(line_ns))
        
        widths  = [width1]      + [width]     *(len(line_ws)-1)
        shifts  = [' '*indent1] + [' '*indent]*(len(line_ws)-1)
            
        # Format lines
        if how=='l':
            return [sh+''.join(ws)
                    for    ws,sh in         zip(line_ws,shifts)]
        if how=='r':
            return [sh
                   +' '*(wd-ns)
                   +''.join(ws)
                    for ns,ws,sh,wd in zip(line_ns,line_ws,shifts,widths)]
        if how=='c':
            return [sh
                   +' '*       int((wd-ns)/2)
                   +''.join(ws)
                   +' '*(wd-ns-int((wd-ns)/2))
                    for ns,ws,sh,wd in zip(line_ns,line_ws,shifts,widths)]
        # Full
        def frm_full(ws, spaces):                           # Spaces needs to append 
            if not spaces:      return ws
            insides = int((len(ws) - 1 )/2)                 # Count of inside space-items: ['w',' ','w',' ','w']
            if not insides:     return ws + [' '*spaces]
            pass;              #LOG and log('ws={}',(ws))
            quant   = max(int(spaces / insides), 1)         # Size  of first  appending q-block
            quants  = min(int(spaces / quant), insides) \
                        if quant else 0                     # Count of first  appending q-block
            extra   =     spaces - quant*quants             # Count of second appending 1-block
            pass;              #LOG and log('(spaces,insides),(quant,quants),extra={}',((spaces,insides),(quant,quants),extra))
            if quants:
                quant_s = ' '*quant
                gap     = max(1, int(insides/quants))
                pass;          #LOG and log('gap={}',(gap))
                for q_i in range(quants):
                    ins = q_i * gap
                    ws[1+2*ins] += quant_s
            if extra:
                gap     = max(1, int(insides/extra))
                pass;          #LOG and log('gap={}',(gap))
                for q_i in range(extra):
                    ins = q_i * gap
                    ws[-2-2*ins] += ' '
            pass;              #LOG and log('ws={}',(ws))
            return ws
           #def frm_full
        
        return     [sh+''.join(frm_full(ws, wd-ns))
                    for ns,ws,sh,wd in zip(line_ns[:-1],line_ws[:-1],shifts[:-1],widths[:-1])] \
                 + [shifts[-1]+''.join(line_ws[-1])]        # Last line has with left format
       #def _form_prph
    
    def _detect_prphs(min_row, max_row):
        pass;                  #LOG and log('min_row, max_row={}',(min_row, max_row))
        pass;                  #return [(min_row, max_row)]
        if min_row>max_row:
            return []
        # Expand/reduce to whole prphs
        def find_row(start, what):
            rsp     = start
            step    = 1 if what=='bot-prph' else -1
            stop    =-1 if what=='top-prph' else ed.get_line_count()
            pass;              #LOG and log('start, stop, step={}',(start, stop, step))
            for row in range(start, stop, step):
                if ''==ed.get_text_line(row).strip():
                    return rsp
                rsp = row
            return rsp
           #def find_row
           
        min_row = find_row(min_row, 'top-prph') #if ''!=ed.get_text_line(min_row).strip() else min_row
        max_row = find_row(max_row, 'bot-prph') #if ''!=ed.get_text_line(max_row).strip() else max_row
        pass;                  #LOG and log('min_row, max_row={}',(min_row, max_row))
        prphs   = []
        top,bot = None,None
        inside  = False
        for row in range(min_row, max_row+1):
            empty   = ''==ed.get_text_line(row).strip()
            if False:pass
            elif not inside and     empty:
                pass
            elif not inside and not empty:
                top     = row
                bot     = row
                inside  = True
            elif     inside and not empty:
                bot     = row
            elif     inside and     empty:
                prphs  += [(top, bot)]
                inside  = False
           #for row
        if inside:
            prphs      += [(top, bot)]
        return prphs
       #def _detect_prphs
        
   #class Prgph_cmds

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
        if app.app_api_version()<FROM_API_VERSION:  return app.msg_status(NEED_UPDATE)
        cons_out= '\n'.join(app.app_log(app.LOG_CONSOLE_GET_MEMO_LINES, ''))
#       cons_out= app.app_log(app.LOG_CONSOLE_GET_LOG, '')
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
    fil_restart_dlg = False
    fil_ed_crts     = None                  # Carets at start
    fil_what        = None                  # String to search 
    @staticmethod
    def dlg_find_in_lines(): #NOTE: dlg_find_in_lines
        Find_repl_cmds.fil_ed_crts  = ed.get_carets()            # Carets at start
        Find_repl_cmds.fil_what     = None
        while True:
            Find_repl_cmds.fil_restart_dlg  = False
            Find_repl_cmds._dlg_FIL()
            if not Find_repl_cmds.fil_restart_dlg:  break
    @staticmethod
    def _dlg_FIL():
#       FORM_C  = f(_('Find in Lines {}'), 1+ed.get_prop(app.PROP_INDEX_GROUP))
        FORM_C  =   _('Find in Lines')
        HELP_C  = _(
            '• Search "in Lines" starts on Enter or Shift+Enter or immediately (if "Instant search" is tuned on).'
          '\r• A found fragment after first caret will be selected.'
          '\r• All found fragments are remembered and dialog can jump over them by [Shift+]Enter or by menu commands.'
          '\r• Option ".*" (regular expression) allows to use Python reg.ex. See "docs.python.org/3/library/re.html".'
          '\r• Option "w" (whole words) is ignored if entered string contains not a word.'
#         '\r• If option "Close on success" (in menu) is tuned on, dialog will close after successful search.'
          '\r• If option "Instant search" (in menu) is tuned on, search result will be updated on start and after each change of pattern.'
          '\r• Command "Restore initial selection" (in menu) restores only first of initial carets.'
          '\r• Ctrl+F (or Ctrl+R) to call appication dialog Find (or Replace).'
        )
        pass;                  #log('###',())
        pass;                  #log('hist={}',(get_hist('find.find_in_lines')))
        opts    = d(reex=False,case=False,word=False,hist=[]           ,usel=False,inst=False,insm=3)
#       opts    = d(reex=False,case=False,word=False,hist=[],clos=False,usel=False,inst=False)
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
                    find_d      = ag.cval('what')
                ,   op_regex_d  = ag.cval('reex')
                ,   op_case_d   = ag.cval('case')
                ,   op_word_d   = ag.cval('word')
                ))
        def do_attr(aid, ag, data=''):
            nonlocal prev_wt
            prev_wt = ''
            return do_find('find', ag, 'stay')  # if opts['inst'] else d(fid='what')
        def do_menu(aid, ag, data=''):
            def wnen_menu(ag, tag):
                nonlocal opts
                if tag in ('clos','usel','inst'):   opts[tag] = not opts[tag]
                if tag=='help':                     app.msg_box(HELP_C, app.MB_OK)
                if tag in ('prev','next'):          return do_find(tag, ag)
                if tag=='rest':
                    ed.set_caret(*Find_repl_cmds.fil_ed_crts[0])
                    return None
                if tag=='insm':
                    insm    = app.dlg_input(_('Instant search minimum'), str(opts['insm']))
                    opts['insm']    = int(insm) if insm and re.match(r'^\d+$', insm) else opts['insm']
                if tag=='inst':
                    Find_repl_cmds.fil_what         = ag.cval('what')
                    Find_repl_cmds.fil_restart_dlg  = True
                    return None
                if tag=='natf':
                    switch_to_dlg(ag)
                    return None
                return []
               #def wnen_menu
            insm_c  = f(_('Instant search minimum: {}...'), opts['insm'])
            ag.show_menu(aid,
                [ d(tag='help'  ,cap=_('&Help...')                                      ,cmd=wnen_menu
                ),d(             cap='-'
                ),d(tag='prev'  ,cap=_('Find &previous')                                ,cmd=wnen_menu  ,key='Shift+Enter'
                ),d(tag='next'  ,cap=_('F&ind next')                                    ,cmd=wnen_menu  ,key='Enter'
                ),d(             cap='-'
#               ),d(tag='clos'  ,cap=_('Close on success')          ,ch=opts['clos']    ,cmd=wnen_menu
                ),d(tag='usel'  ,cap=_('Use selection from text')   ,ch=opts['usel']    ,cmd=wnen_menu
                ),d(tag='inst'  ,cap=_('Instant search')            ,ch=opts['inst']    ,cmd=wnen_menu
                ),d(tag='insm'  ,cap=insm_c                                             ,cmd=wnen_menu
                ),d(             cap='-'
                ),d(tag='natf'  ,cap=_('Call native Find dialog')                       ,cmd=wnen_menu  ,key='Ctrl+F'
                ),d(tag='rest'  ,cap=_('Restore initial selection and close dialog &=') ,cmd=wnen_menu  ,key='Shift+Esc'
                )]
            )
            return d(fid='what')
           #def do_menu
        def do_find(aid, ag, data=''):
            nonlocal opts, prev_wt, ready_l, ready_p
            pass;              #log('aid, data={}',(aid, data))
            # What/how will search
            prnx    = 'prev' if aid=='prev' else 'next'
            crt     = ed.get_carets()[0][:]     # Current first caret (col,row, col?,row?)
            min_rc  = (crt[1], crt[0])  if crt[2]==-1 else  min((crt[1], crt[0]), (crt[3], crt[2]))
            max_rc  = (crt[1], crt[0])  if crt[2]==-1 else  max((crt[1], crt[0]), (crt[3], crt[2]))
            what    = ag.cval('what')
            if prev_wt==what and ready_l:# and 'stay' not in data:
                pass;          #log('will jump',())
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
            opts.update(ag.cvals(['reex','case','word']))
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
#                   if opts['clos']:
#                       select_frag(fnd_end, row, fnd_bgn, row)
#                       return None         # Close dlg
                    ready_p = (len(ready_l)
                                if prnx=='next' and ready_p==-1 and                             # Need next and no yet
                                    (row>max_rc[0] or row==max_rc[0] and fnd_bgn>max_rc[1])     # At more row or at more col in cur row
                                or prnx=='prev'                 and                             # Need prev
                                    (row<min_rc[0] or row==min_rc[0] and fnd_end<min_rc[1])     # At less row or at less col in cur row
                                else ready_p)
                    ready_l+= [(fnd_end, row, fnd_bgn, row)]
            pass;              #log('ready_l={}',(ready_l))
            ready_p = max(0, ready_p) if ready_l else -1
            pass;              #log('ready_p={}',(ready_p))
            # Show results
            if ready_l:
                if aid=='find' and 'stay' in data:
                    ready_p = (ready_p-1) % len(ready_l)
                pass;          #log('show rslt ready_p={}',(ready_p,))
                select_frag(ready_l[ready_p])
            return d(ctrls=[('what',d(items=opts['hist']))]
                    ,form=d(cap=form_cap())
                    ,fid='what')
           #def do_find
        what    = Find_repl_cmds.fil_what   if Find_repl_cmds.fil_what is not None      else \
                  ed.get_text_sel()         if opts['usel'] and 1==len(ed.get_carets()) else ''
        what    = '' if '\r' in what or '\n' in what else what
        ag      = None
        def do_key_down(idd, idc, data=''):
            scam    = data if data else app.app_proc(app.PROC_GET_KEYSTATE, '')
            if 0:pass
            elif (scam,idc)==('s',VK_ENTER):        # Shift+Enter
                ag._update_on_call(do_find('prev', ag))
            elif (scam,idc)==('s',VK_ESCAPE):       # Shift+Esc
                ed.set_caret(*Find_repl_cmds.fil_ed_crts[0])
                ag.hide()
            elif (scam,idc)==('c',ord('F')) or (scam,idc)==('c',ord('R')):        # Ctrl+F or Ctrl+R
                switch_to_dlg(ag, 'find' if idc==ord('F') else 'repl')
            else: return
            return False
        wh_tp   = 'ed'      if opts['inst'] else 'cb'
        wh_call = do_find   if opts['inst'] else None
        ag      = DlgAgent(
            form    =dict(cap=form_cpw(), w=255, h=35, h_max=35
                         ,on_key_down=do_key_down
                         ,border=app.DBORDER_SIZE
                         ,resize=True)
        ,   ctrls   =[0
    ,('find',d(tp='bt'  ,t=0        ,l=-99      ,w=44   ,cap=''     ,sto=False  ,def_bt='1'         ,call=do_find           ))  # Enter
    ,('reex',d(tp='chb' ,tid='what' ,l=5+38*0   ,w=39   ,cap='.&*'  ,hint=_('Regular expression')   ,call=do_attr           ))  # &*
    ,('case',d(tp='chb' ,tid='what' ,l=5+38*1   ,w=39   ,cap='&aA'  ,hint=_('Case sensitive')       ,call=do_attr           ))  # &a
    ,('word',d(tp='chb' ,tid='what' ,l=5+38*2   ,w=39   ,cap='"&w"' ,hint=_('Whole words')          ,call=do_attr           ))  # &w
    ,('what',d(tp=wh_tp ,t  =5      ,l=5+38*3+5 ,w=85   ,items=opts['hist']                         ,call=wh_call   ,a='lR' ))  # 
    ,('menu',d(tp='bt'  ,tid='what' ,l=210      ,w=40   ,cap='&='                   ,on_menu=do_menu,call=do_menu   ,a='LR' ))  # &=
                    ][1:]
        ,   fid     ='what'
        ,   vals    = upd_dict({k:opts[k] for k in ('reex','case','word')}, d(what=what))
                              #,options={'gen_repro_to_file':'repro_dlg_find_in_lines.py'}
        )
        if opts['inst'] and what:
            ag._update_on_call(do_find('find', ag, 'stay'))
        ag.show(lambda ag: set_hist('find.find_in_lines', upd_dict(opts, ag.cvals(['reex','case','word']))))
       #def _dlg_FIL

    @staticmethod
    def find_cb_by_cmd(updn):
        if app.app_api_version()<FROM_API_VERSION:  return app.msg_status(NEED_UPDATE)
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

    @staticmethod
    def replace_all_sel_to_cb():
        if app.app_api_version()<FROM_API_VERSION:  return app.msg_status(NEED_UPDATE)
        crts    = ed.get_carets()
        if len(crts)>1: return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
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
        pass;                  #log('seltext,clip,find_opt={}',(seltext,clip,find_opt))
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

#   @staticmethod
#   def find_dlg_adapter(act):
##       try:
##           foo=1/0
##       except Exception as ex:
##           return
##       pass;                   app.msg_status('No release yet (waiting API update)')
##       pass;                   return
#       if app.app_api_version()<'1.0.144': return app.msg_status(NEED_UPDATE)
#       find_ss = app.app_proc(app.PROC_GET_FIND_STRINGS, '')
#       if not find_ss:                     return app.msg_status(_('Use Find/Replace dialog before'))
#       user_wht= find_ss[0] if find_ss else ''
#       user_rep= find_ss[1] if find_ss else ''
#       user_opt= app.app_proc(app.PROC_GET_FIND_OPTIONS, '')
#       # c - Case, r - RegEx,  w - Word,  f - From-caret,  a - Wrap
#       cmd_id  = apx.icase(False,''
#               ,   act=='mark'      , 'findmark'
#               ,   act=='count'     , 'findcnt'
#               ,   act=='find-first', 'findfirst'
#               ,   act=='find-next' , 'findnext'
#               ,   act=='find-prev' , 'findprev'
#               ,   act=='repl-next' , 'rep'
#               ,   act=='repl-stay' , 'repstop'
#               ,   act=='repl-all'  , 'repall'
#               )
#       cmd_opt = apx.icase(False,''
#               ,   act=='find-first' and 'f' in user_opt,  user_opt.replace('f', '')
#               ,   user_opt
#               )
#       pass;                  #LOG and log('cmd_id,user_opt,cmd_opt,user_wht,user_rep={}',(cmd_id,user_opt,cmd_opt,user_wht,user_rep))
##       cmd_par = c1.join([]
##                           +[cmd_id]
##                           +[user_wht]
##                           +[user_rep]
##                           +[cmd_opt]  # a - wrapped
##                           )
##       pass;                   LOG and log('cmd_par={}',repr(cmd_par))
##       ed.cmd(cmds.cmd_FinderAction, cmd_par)
#       ed.cmd(cmds.cmd_FinderAction, c1.join([]
#           +[cmd_id]
#           +[user_wht]
#           +[user_rep]
#           +[cmd_opt]  # a - wrapped
#       ))
#       app.app_proc(app.PROC_SET_FIND_OPTIONS, user_opt)
#      #def find_dlg_adapter
       
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
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
        (cCrt, rCrt
        ,cEnd, rEnd)    = crts[0]
        if rEnd==-1 or rEnd==rCrt:
            return app.msg_status(ONLY_FOR_ML_SEL.format(_('Command')))
        spr     = app.dlg_input('Enter separator string', Find_repl_cmds.data4_align_in_lines_by_sep)
        spr     = '' if spr is None else spr.strip()
        if not spr:
            return # Esc
        Find_repl_cmds.data4_align_in_lines_by_sep    = spr
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

    @staticmethod
    def reindent():
        if app.app_api_version()<MIN_API_VER_4_REPL: return app.msg_status(_('Need update application'))
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
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
        fid         = 'olds'
        while True:
            btn,vals,_t,_p = dlg_wrapper(f(_('Reindent selected lines ({})'), rSelE-rSelB+1), 245,120,     #NOTE: dlg-reindent
                 [dict(           tp='lb'   ,tid='olds' ,l=5        ,w=150  ,cap='>'+_('&Old indent step:') ,hint=fill_h) # &o
                 ,dict(cid='olds',tp='ed'   ,t=10       ,l=5+150+5  ,w= 80                                              ) # 
                 ,dict(           tp='lb'   ,tid='news' ,l=5        ,w=150  ,cap='>'+_('&New indent step:') ,hint=fill_h) # &n
                 ,dict(cid='news',tp='ed'   ,t=50       ,l=5+150+5  ,w= 80                                              )
#                ,dict(cid='?'   ,tp='bt'   ,t=90       ,l=5        ,w= 30  ,cap='&?'                                   ) #   
                 ,dict(cid='!'   ,tp='bt'   ,t=90       ,l=245-170-5,w= 80  ,cap=_('OK')                    ,def_bt='1' ) #   
                 ,dict(cid='-'   ,tp='bt'   ,t=90       ,l=245-80-5 ,w= 80  ,cap=_('Cancel')                            )
                 ],    vals, focus_cid=fid)
            if btn is None or btn=='-': return None
            if ''==vals['olds'] or vals['olds'][0] not in ' .t2345678':
                app.msg_box(_('Fill "Old step".\n\n'+fill_h.replace('\r', '\n')), app.MB_OK)
                fid = 'olds'
                continue
            if ''==vals['news'] or vals['news'][0] not in ' .t2345678':
                app.msg_box(_('Fill "New step".\n\n'+fill_h.replace('\r', '\n')), app.MB_OK)
                fid = 'news'
                continue
            old_s   = parse_step(vals['olds'].replace('.', ' '))
            new_s   = parse_step(vals['news'].replace('.', ' '))
            pass;                  #LOG and log('old_s, new_s={}',(old_s, new_s))
            if not old_s or not new_s or old_s==new_s:
                return app.msg_status(_('Reindent skipped'))
            break
           #while
        
        lines   = [ed.get_text_line(row) for row in range(rSelB, rSelE+1)]
        def reind_line(line, ost_l, nst):
            pass;              #LOG and log('line={}',repr(line))
            if not line.startswith(ost_l[0]):    return line
            for n in range(1, 1000):
                if n == len(ost_l):
                    ost_l.append(ost_l[0]*n)
                if not line.startswith(ost_l[n]):
                    break
            pass;              #LOG and log('n,len(ost_l[n-1])={}',(n,len(ost_l[n-1])))
            new_line    = nst*n + line[len(ost_l[n-1]):]
            pass;              #LOG and log('new={}',repr(new_line))
            return new_line
        ost_l   = [old_s*n for n in range(1,20)]
        lines   = [reind_line(l, ost_l, new_s) for l in lines]
        pass;                   LOG and log('rSelB, rSelE, lines={}',(rSelB, rSelE, lines))
        ed.replace_lines(rSelB, rSelE, lines)
#       Find_repl_cmds._replace_lines(ed, rSelB, rSelE, '\n'.join(lines))
        ed.set_caret(0,rSelE+1, 0,rSelB)
       #def reindent
    
    @staticmethod
    def indent_sel_as_1st():
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
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
    
    @staticmethod
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
    
    @staticmethod
    def align_sel_by_margin(how):
        pass;                   log('ok',())
        if not apx.get_opt('tab_spaces', False):
            return app.msg_status(_('Fail to use Tab to align'))
        mrgn    = apx.get_opt('margin', 0)
        pass;                   log('mrgn={}',(mrgn))
        def align_line(line):
            strpd   = line.strip()
            lstr    = len(strpd)
            if lstr >= mrgn:
                pass;           log('lstr >= mrgn',())
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

#   @staticmethod
#   def split_lines_to_width():
#       width   = apx.get_opt('last_width_for_split_lines', apx.get_opt('margin', 0))
#       width   = app.dlg_input(_('Width for split lines'), str(width))
#       if not width or not width.isdigit() or not (0<int(width)<1000):
#           app.msg_status(_('Skip to split lines'))
#       apx.set_opt('last_width_for_split_lines', width)
#      #def split_lines_to_width
    
    @staticmethod
    def join_lines():
        if app.app_api_version()<MIN_API_VER_4_REPL: return app.msg_status(_('Need update application'))
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
        (cCrt, rCrt
        ,cEnd, rEnd)    = crts[0]
        (rSelB, cSelB), \
        (rSelE, cSelE)  = apx.minmax((rCrt, cCrt), (rEnd, cEnd))
        rSelE           = rSelE - (1 if 0==cSelE else 0)
        if rEnd==-1 or rEnd==rCrt or rSelB==rSelE:
            return app.msg_status(ONLY_FOR_ML_SEL.format(_('Command')))
        first_ln= ed.get_text_line(rSelB)
        last_ln = ed.get_text_line(rSelE)
        lines   = [first_ln.rstrip()] \
                + [ed.get_text_line(row).strip() for row in range(rSelB+1, rSelE)] \
                + [last_ln.lstrip()]
        joined  = ' '.join(l for l in lines if l)
#       ed.delete(0,rSelB, len(last_ln),rSelE)
#       ed.insert(0,rSelB, joined+'\n')
##       ed.insert(0,rMin, joined+'\n')
        Find_repl_cmds._replace_lines(ed, rSelB, rSelE, joined)
        ed.set_caret(0,rSelB+1, 0,rSelB)
       #def join_lines
    
    @staticmethod
    def del_more_spaces():
        if app.app_api_version()<MIN_API_VER_4_REPL: return app.msg_status(_('Need update application'))
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
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
    
    @staticmethod
    def _rewrap(margin, cmt_sgn, save_bl, rTx1, rTx2, sel_after):
    
        tab_sz  = apx.get_opt('tab_size', 8)
        lines   = [ed.get_text_line(nln) for nln in range(rTx1, rTx2+1)]
        pass;                   LOG and log('lines={}',(lines))
        # Extract prefix by comment-sign
        cm_prfx = ''
        if lines[0].lstrip().startswith(cmt_sgn):
            # First line commented - need for all
            cm_prfx = lines[0][:lines[0].index(cmt_sgn)+len(cmt_sgn)]
            if not all(map(lambda l:l.startswith(cm_prfx), lines)):
                return app.msg_status('Re-wrap needs same positions of comments')
        pass;                  #LOG and log('1 cm_prfx={}',repr(cm_prfx))
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
        pass;                   LOG and log('2 cm_prfx={}',repr(cm_prfx))
        if len(cm_prfx)+10>margin:
            return app.msg_status('No text to re-wrap')
        # Join
        lines   = [line[len(cm_prfx):] for line in lines]
        if not save_bl:
            lines   = [line.lstrip() for line in lines]
        text    = ' '.join(lines)
        pass;                   LOG and log('mid text={}',('\n'+text))
        # Split by margin
        margin -= (len(cm_prfx) + (tab_sz-1)*cm_prfx.count('\t'))
        pass;                   LOG and log('margin,tab_sz={}',(margin,tab_sz))
        words   = [(m.start(), m.end(), m.group())
                    for m in re.finditer(r'\b\S+\b', text)]
        pass;                  #LOG and log('words={}',(words))
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
        pass;                   LOG and log('fin text={}',('\n'+text))
        # Modify ed
        Find_repl_cmds._replace_lines(ed, rTx1, rTx2, text)
#       ed.delete(0,rTx1, 0,rTx2+1)
#       ed.insert(0,rTx1, text+'\n')
        if sel_after:
            ed.set_caret(0,rTx1+len(lines), 0,rTx1)
       #def _rewrap

    @staticmethod
    def rewrap_cmt_at_caret():
        if app.app_api_version()<MIN_API_VER_4_REPL: return app.msg_status(_('Need update application'))
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
        
        Find_repl_cmds._rewrap(margin, cmt_sgn, True, line1, line2, False)
       #def rewrap_cmt_at_caret

    @staticmethod
    def rewrap_sel_by_margin():
        if app.app_api_version()<MIN_API_VER_4_REPL: return app.msg_status(_('Need update application'))
        margin  = apx.get_opt('margin', 0)
        lex     = ed.get_prop(app.PROP_LEXER_FILE, '')
#       cmt_sgn = app.lexer_proc(app.LEXER_GET_COMMENT, lex)            if lex else ''
        cmt_sgn = app.lexer_proc(app.LEXER_GET_PROP, lex)['c_line']     if lex else ''
        aid,vals,_t,chds   = dlg_wrapper(_('Re-wrap lines'), 5+165+5,5+120+5,     #NOTE: dlg-rewrap
             [dict(           tp='lb'   ,tid='marg' ,l=5        ,w=120  ,cap=_('&Margin:')      ) # &m
             ,dict(cid='marg',tp='ed'   ,t=5        ,l=5+120    ,w=45                           ) # 
             ,dict(           tp='lb'   ,tid='csgn' ,l=5        ,w=120  ,cap=_('&Comment sign:')) # &c
             ,dict(cid='csgn',tp='ed'   ,t=5+30     ,l=5+120    ,w=45                           )
             ,dict(cid='svbl',tp='ch'   ,t=5+60     ,l=5        ,w=165  ,cap=_('&Keep indent')  ) # &s
             ,dict(cid='!'   ,tp='bt'   ,t=5+120-28 ,l=5        ,w=80   ,cap=_('OK'),  props='1') #     default
             ,dict(cid='-'   ,tp='bt'   ,t=5+120-28 ,l=5+80+5   ,w=80   ,cap=_('Cancel')        )
             ],    dict(marg=str(margin)
                       ,csgn=cmt_sgn
                       ,svbl=True), focus_cid='marg')
        if aid is None or aid=='-': return None
        if not vals['marg'].isdigit(): return app.msg_status('Not digit margin')
        margin  = int(vals['marg'])
        cmt_sgn =     vals['csgn']
        save_bl =     vals['svbl']
        
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
        cCrt, rCrt, \
        cEnd, rEnd  = crts[0]
        cEnd, rEnd  = (cCrt, rCrt) if -1==rEnd else (cEnd, rEnd)
        (rTx1,cTx1),\
        (rTx2,cTx2) = apx.minmax((rCrt, cCrt), (rEnd, cEnd))
        rTx2        = rTx2-1 if cTx2==0 and rTx1!=rTx2 else rTx2
        pass;                   LOG and log('rTx1, rTx2={}',(rTx1, rTx2))

        Find_repl_cmds._rewrap(margin, cmt_sgn, save_bl, rTx1, rTx2, True)
       #def rewrap_sel_by_margin
        
    @staticmethod
    def _replace_lines(_ed, r_bgn, r_end, newlines):
        """ Replace full lines in [r_bgn, r_end] to newlines """
        if app.app_api_version()<MIN_API_VER_4_REPL: return app.msg_status(_('Need update application'))
        lines_n     = _ed.get_line_count()
        pass;                   LOG and log('lines_n, r_bgn, r_end, newlines={}',(lines_n, r_bgn, r_end, newlines))
        if r_end < lines_n-1:
            # Replace middle lines
            pass;               LOG and log('middle',())
            _ed.delete(0,r_bgn, 0,1+r_end)
            _ed.insert(0,r_bgn, newlines+'\n')
        else:
            # Replace final lines
            pass;               LOG and log('final',())
            _ed.delete(0,r_bgn, 0,lines_n)
            _ed.insert(0,r_bgn, newlines)
       #def _replace_lines
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
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
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
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))

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

    @staticmethod
    def paste_trimmed():
        clip = app.app_proc(app.PROC_GET_CLIP, '')
        if not clip.strip():
            return msg_status(_('Clipboard has no text'))
        clip = '\n'.join(l.strip() for l in clip.splitlines())
        
        crts = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
        
        x1, y1, x2, y2 = crts[0]
        if y2>=0:
            if (y1, x1)>(y2, x2):
                x1, y1, x2, y2 = x2, y2, x1, y1
            ed.delete(x1, y1, x2, y2)
            clip += ('\n' if y1!=y2 and x2==0 else '') # To avoid bug in ed.insert
        x, y = ed.insert(x1, y1, clip)
        ed.set_caret(x, y)

        app.msg_status(_('Pasted trimmed text'))
       #def paste_trimmed

    @staticmethod
    def trim_sel(mode):
        crts = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
    
        x1, y1, x2, y2 = crts[0]
        if y2<0:
            return msg_status('Need selection')
        
        if (y1, x1)>(y2, x2):
            x1, y1, x2, y2 = x2, y2, x1, y1
        
        text = ed.get_text_substr(x1, y1, x2, y2)
        trimmer = lambda s:(s.lstrip()   if mode=='left'  else
                            s.rstrip()   if mode=='right' else
                            s.strip()   #if mode=='all'
                           )
        text2 = '\n'.join(trimmer(l) for l in text.splitlines())
        if text==text2:
            return app.msg_status(_('Text already trimmed'))
        text2 += ('\n' if x2==0 else '')    # To avoid bug in ed.replace
        
        x3, y3 = ed.replace(x1, y1, x2, y2, text2)
        ed.set_caret(x1, y1, x3, y3)
        app.msg_status(_('Text trimmed'))
       #def trim_sel

    @staticmethod
    def fill_by_str():
        crts    = ed.get_carets()
        if all(-1==cEnd for cCrt, rCrt, cEnd, rEnd in crts):    return
        str2fill    = app.dlg_input('Enter string to fill selection', '')
        if not str2fill:    return
        cnt = 0
        for cCrt, rCrt, cEnd, rEnd in crts:
            if -1  ==cEnd:    continue
            if rCrt!=rEnd:    continue
            ((rSelB, cSelB)
            ,(rSelE, cSelE))= apx.minmax((rCrt, cCrt), (rEnd, cEnd))
            trg_len = cSelE - cSelB
            trg_str = str2fill * (1  + int(trg_len/len(str2fill)))
            trg_str = trg_str[:trg_len]
            ed.replace(cSelB, rSelB, cSelE, rSelE, trg_str)
            cnt += 1
           #for
        if cnt>0:
            app.msg_status(_('Changed %d selection(s)')%cnt)
        else:
            app.msg_status(_('Need single-line selection(s)'))
        pass;                   LOG and log('ok',())
       #def fill_by_str

    @staticmethod
    def insert_char_by_hex():
        hexcode = app.dlg_input('Unicode hex code:     0xhhhh  or  hhhh  or  hh', '')
        if not hexcode:
            return
        if not (len(hexcode) in (2, 4, 6) and
                re.search(r'(0x)?[\dabcdef]+', hexcode)
               ):
            app.msg_status('Not valid hex code: ' + hexcode)
            return

        hexcode = hexcode.upper()
        hexcode = hexcode[2:]   if hexcode.startswith('0X') else hexcode
        hexcode = '00'+hexcode  if len(hexcode)==2          else hexcode

        try:
            text = chr(int(hexcode, 16))
        except:
            app.msg_status('Not valid hex code: ' + hexcode)
            return

        #this supports multi-carets on insert
        ed.cmd(cmds.cCommand_TextInsert, text)
        app.msg_status('Char inserted: U+' + hexcode)
       #def insert_char_by_hex
    
   #class Insert_cmds
    
class Command:
#   def __init__(self):
        # Data for go_back_tab with "visit history"
#       self.cur_tab_id = None
#       self.pre_tab_id = None
#       self.tid_hist   = deque((), apx.get_opt('ui_max_history_edits', 20))  # append to left, scan from left, loose from right
       #def __init__
        
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
        if app.app_api_version()<FROM_API_VERSION:  return app.msg_status(NEED_UPDATE)
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
        id_splt = {'L': app.SPLITTER_SIDE
                  ,'B': app.SPLITTER_BOTTOM
                  ,'G1':app.SPLITTER_G1
                  ,'G2':app.SPLITTER_G2
                  ,'G3':app.SPLITTER_G3
                  }[id_splt]

        (vh, shown, pos_old, prn_size)  = app.app_proc(app.PROC_SPLITTER_GET, id_splt)
        pass;                  #LOG and log('vh, shown, pos_old, prn_size={}',(vh, shown, pos_old, prn_size))
#       (vh, shown, pos_old, prn_size)  = app.app_proc(app.PROC_GET_SPLIT, id_splt)
        pass;                  #LOG and log('id_splt, vh, shown, pos_old, prn_size={}',(id_splt, vh, shown, pos_old, prn_size))
        if not shown:           return
        pos_new     = int(factor * pos_old)
        pass;                  #LOG and log('pos_new={}',(pos_new))
        pos_new     = max(100, min(prn_size-100, pos_new))
        pass;                  #LOG and log('pos_new={}',(pos_new))
        if pos_new==pos_old:    return
        pass;                  #LOG and log('id_splt, pos_new={}',(id_splt, pos_new))
        app.app_proc(app.PROC_SPLITTER_SET, (id_splt, pos_new))
#       app.app_proc(app.PROC_SET_SPLIT, '{};{}'.format(id_splt, pos_new))
       #def _move_splitter

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
            btn,vals,_t,chds   = dlg_wrapper(_('Rename file'), GAP+300+GAP,GAP+80+GAP,     #NOTE: dlg-rename
                 [dict(           tp='lb'   ,t=GAP          ,l=GAP          ,w=200      ,cap=_('Enter new file name:')  ) # &e
                 ,dict(cid='stem',tp='ed'   ,t=GAP+18       ,l=GAP          ,w=200+10                                   ) # 
                 ,dict(           tp='lb'   ,tid='stem'     ,l=GAP+200+12   ,w=8        ,cap='.'                        ) # &.
                 ,dict(cid='sext',tp='ed'   ,tid='stem'     ,l=GAP+200+20   ,w=80                                       )
                 ,dict(cid='!'   ,tp='bt'   ,t=GAP+80-28    ,l=GAP+300-170  ,w=80       ,cap=_('OK'),  props='1'        ) #     default
                 ,dict(cid='-'   ,tp='bt'   ,t=GAP+80-28    ,l=GAP+300-80   ,w=80       ,cap=_('Cancel')                )
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

    def reopen_as(self, how):
        fn  = ed.get_filename()
        if not fn or ed.get_prop(app.PROP_MODIFIED):
            return app.msg_status(_('Save file first'))
        
        if app.app_api_version()<'1.0.238':
            return app.msg_status(NEED_UPDATE)
        kind_f  = ed.get_prop(app.PROP_KIND)
        kind_v  = ed.get_prop(app.PROP_V_MODE)
        if how=='text' and kind_f=='text'                          \
        or how=='hex'  and kind_f=='bin'  and kind_v==app.VMODE_HEX:
            return app.msg_status(_('No need to do anything'))
            
        ed.cmd(cmds.cmd_FileClose)
        if 0:pass
        elif how=='text':
            app.file_open(fn)
            app.msg_status(_('Reopened in text editor'))
        elif how=='hex':
            app.file_open(fn, options='/view-hex')
            app.msg_status(_('Reopened in hex viewer'))
       #def reopen_as

    def new_file_save_as_near_cur(self):
        cur_fn  = ed.get_filename()
        if not cur_fn:  return app.msg_status(_('Warning: the command needs a named tab.'))
        cur_dir = os.path.dirname(cur_fn)
        new_fn  = app.dlg_file(False, '', cur_dir, '')
        if not new_fn:  return
        app.file_open('')
        ed.save(new_fn)
       #def new_file_save_as_near_cur

    def open_recent(self):
        home_s      = os.path.expanduser('~')
        hist_fs_f   = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'history files.json'
        if not os.path.exists(hist_fs_f):   return app.msg_status(_('No files in history'))
        hist_full_js= json.loads(open(hist_fs_f, encoding='utf8').read())
        hist_fs     = [f.replace('|', os.sep) for f in hist_full_js]
        hist_fts    = [(f.replace(home_s, '~'), os.path.getmtime(f))
                        for f in hist_fs if os.path.exists(f)]
        sort_as     = get_hist([           'open-recent','sort_as'],
                      apx.get_opt('cuda_ext.open-recent.sort_as',    't'))
        show_as     = get_hist([           'open-recent','show_as'],
                      apx.get_opt('cuda_ext.open-recent.show_as',    'n'))
        while True:
            hist_fts    = sorted(hist_fts
                                , key=lambda ft:(ft[1]          if sort_as=='t' else
                                                 ft[0].upper()  if show_as=='p' else
                                                 os.path.basename(ft[0]).upper()
                                                )
                                , reverse=(sort_as=='t'))
            ans         = app.dlg_menu(app.MENU_LIST, '\n'.join([
                            (fn if show_as=='p' else
                             f('{} ({})', os.path.basename(fn), os.path.dirname(fn)))
                            + '\t'
                            + time.strftime("%Y/%b/%d %H:%M", time.gmtime(tm))
                            for fn,tm in hist_fts
                          ]
                          +['<Show "name (path)">'  if show_as=='p' else
                            '<Show "path/name">']
                          +['<Sort by path>'        if sort_as=='t' and show_as=='p' else
                            '<Sort by name>'        if sort_as=='t' and show_as=='n' else
                            '<Sort by time>']
                                                               )
                                      )
            if ans is None: return
            if ans==(0+len(hist_fts)):
                show_as     = 'p' if show_as=='n' else 'n'
                set_hist(['open-recent','show_as'], show_as)
                continue #while
            if ans==(1+len(hist_fts)):
                sort_as     = 'p' if sort_as=='t' else 't'
                set_hist(['open-recent','sort_as'], sort_as)
                continue #while
            return app.file_open(hist_fts[ans][0].replace('~', home_s))
#           break#while
           #while
       #def open_recent

    def open_all_with_subdir(self):
        src_dir = app.dlg_dir(os.path.dirname(ed.get_filename()))
        if not src_dir: return
        masks   = app.dlg_input(_('Mask(s) for filename ("*" - all files; "*.txt *.bat" - two masks)'), '*')
        if not masks: return
        masks   = re.sub(r'\s\s+', ' ', masks)
        masks   = masks.split(' ')
        files   = []
        dirs    = set()
        for dirpath, dirnames, filenames in os.walk(src_dir):
            dir_fs  = [dirpath+os.sep+fn for fn in filenames
                        if any(map(lambda mask:fnmatch(fn, mask), masks))]
#           dir_fs  = [dirpath+os.sep+fn for fn in filenames
#                       if fnmatch(fn, mask)]
            if dir_fs:
                files  += dir_fs
                dirs.add(dirpath)

        pass;                  #LOG and log('dirs={}',(dirs))
        if app.ID_OK!=app.msg_box(
            f(_('Open {} file(s) from {} folder(s)?{}'), len(files), len(dirs), '\n   '+'\n   '.join(
                files
                    if len(files) < 5*2+2 else
                files[:5] + ['...'] + files[-5:]
            ))
            , app.MB_OKCANCEL ):   return
            
        for (i, fn) in enumerate(files):
            if i%8 == 0:
                app.app_idle()
            app.app_proc(app.PROC_PROGRESSBAR, i * 100 // len(files))
            app.file_open(fn)
        app.app_proc(app.PROC_PROGRESSBAR, -1)
       #def open_all_with_subdir
    
    def open_with_defapp(self):
        if not os.name=='nt':       return app.msg_status(_('Command is for Windows only.'))
        cf_path     = ed.get_filename()
        if not cf_path:             return app.msg_status(_('No file to open. '))
        if ed.get_prop(app.PROP_MODIFIED) and \
            app.msg_box(  _('Text is modified!'
                          '\nCommand will use file content from disk.'
                        '\n\nContinue?')
                           ,app.MB_YESNO+app.MB_ICONQUESTION
                           )!=app.ID_YES:   return
        try:
            os.startfile(cf_path)
        except Exception as ex:
            pass;               log(traceback.format_exc())
            return app.msg_status(_('Error: '+ex))
       #def open_with_defapp
    
    def save_tabs_to_file(self):
        RES_ALL = 0
        RES_VIS = 1
        RES_SEP = 3
        RES_OK = 4
        
        res = app.dlg_custom('Save editors to a single file',
            410, 175,
            '\n'.join([
                'type=radio\1cap=Save all tabs (including not visible)\1pos=10,10,400,0\1val=1',    
                'type=radio\1cap=Save visible editors in all groups\1pos=10,35,400,0',
                'type=label\1cap=Separator line:\1pos=10,65,400,0',    
                'type=edit\1val=-----\1pos=10,90,400,0',
                'type=button\1cap=&OK\1pos=100,140,200,0',    
                'type=button\1cap=Cancel\1pos=210,140,310,0'    
            ]),
            get_dict=True
            )
        if res is None: return
        if res['clicked']!=RES_OK: return
        
        res_all = res[RES_ALL]=='1'
        res_sep = res[RES_SEP]
    
        if res_all:
            eds = [app.Editor(h) for h in app.ed_handles()]
        else:
            MAX_GROUPS = 6
            eds = [app.ed_group(i) for i in range(MAX_GROUPS)]
            eds = [i for i in eds if i]
        
        fn = app.dlg_file(False, 'saved.txt', '', '')
        if not fn:
            return 
            
        txt = ('\n'+res_sep+'\n').join([e.get_text_all() for e in eds])
        with open(fn, 'w', encoding='utf8') as f:
            f.write(txt)
        app.msg_status('Saved: '+fn)
       #def save_tabs_to_file
    
    def remove_unprinted(self):
        body    = ed.get_text_all()
        in_size = len(body)
        for ichar in range(32):
            if not ichar in [9,10,13]:
                body    = body.replace(chr(ichar), '')
        ed.set_text_all(body)   if in_size != len(body) else None
        app.msg_status(f(_('Removed characters: {}'), in_size-len(body)))
       #def remove_unprinted
    
    def remove_xml_tags(self):
        rxCmt   = re.compile('<!--.*?-->', re.DOTALL)
        rxTag   = re.compile('<.*?>', re.DOTALL)
        body    = ed.get_text_all()
        if not rxCmt.search(body) and not rxTag.search(body):
            return app.msg_status(_('No tags'))
        cmts    = rxCmt.findall(body)
        body    = rxCmt.sub('', body)
        tags    = rxTag.findall(body)
        body    = rxTag.sub('', body)
        ed.set_text_all(body)
        app.msg_status(
            f(_('Stripping is done. Removed tags: {}'), len(tags))
                if not cmts else
            f(_('Stripping is done. Removed comments: {}, removed tags: {}'), len(cmts), len(tags))
        )
       #def remove_xml_tags
    
    def on_console_nav(self, ed_self, text):    return Nav_cmds.on_console_nav(ed_self, text)
    def _open_file_near(self, where='right'):   return Nav_cmds._open_file_near(where)
    def open_selected(self):                    return Nav_cmds.open_selected()
    def nav_by_console_err(self):               return Nav_cmds.nav_by_console_err()
    
    def tree_path_to_status(self):              return Tree_cmds.tree_path_to_status()
    def set_nearest_tree_node(self):            return Tree_cmds.set_nearest_tree_node()
    def find_tree_node(self):                   return Tree_cmds.find_tree_node()
    
    def add_indented_line_above(self):          return Insert_cmds.add_indented_line_above()
    def add_indented_line_below(self):          return Insert_cmds.add_indented_line_below()
    def paste_to_1st_col(self):                 return Insert_cmds.paste_to_1st_col()
    def paste_with_indent(self, where='above'): return Insert_cmds.paste_with_indent(where)
    def paste_trimmed(self):                    return Insert_cmds.paste_trimmed()
    def trim_sel(self, mode):                   return Insert_cmds.trim_sel(mode)
    def fill_by_str(self):                      return Insert_cmds.fill_by_str()
    def insert_char_by_hex(self):               return Insert_cmds.insert_char_by_hex()
    
    def dlg_find_in_lines(self):                return Find_repl_cmds.dlg_find_in_lines()
    def find_cb_string_next(self):              return Find_repl_cmds.find_cb_by_cmd('dn')
    def find_cb_string_prev(self):              return Find_repl_cmds.find_cb_by_cmd('up')
    def replace_all_sel_to_cb(self):            return Find_repl_cmds.replace_all_sel_to_cb()
    def align_in_lines_by_sep(self):            return Find_repl_cmds.align_in_lines_by_sep()
    def reindent(self):                         return Find_repl_cmds.reindent()
    def indent_sel_as_1st(self):                return Find_repl_cmds.indent_sel_as_1st()
    def indent_sel_as_bgn(self):                return Find_repl_cmds.indent_sel_as_bgn()
    def rewrap_sel_by_margin(self):             return Find_repl_cmds.rewrap_sel_by_margin()
    def rewrap_cmt_at_caret(self):              return Find_repl_cmds.rewrap_cmt_at_caret()
    def align_sel_by_margin(self,how):          return Find_repl_cmds.align_sel_by_margin(how)
    def join_lines(self):                       return Find_repl_cmds.join_lines()
    def del_more_spaces(self):                  return Find_repl_cmds.del_more_spaces()

#   def mark_all_from(self):                    return Find_repl_cmds.find_dlg_adapter('mark')
#   def count_all_from(self):                   return Find_repl_cmds.find_dlg_adapter('count')
#   def find_first_from(self):                  return Find_repl_cmds.find_dlg_adapter('find-first')
#   def find_next_from(self):                   return Find_repl_cmds.find_dlg_adapter('find-next')
#   def find_prev_from(self):                   return Find_repl_cmds.find_dlg_adapter('find-prev')
#   def repl_next_from(self):                   return Find_repl_cmds.find_dlg_adapter('repl-next')
#   def repl_stay_from(self):                   return Find_repl_cmds.find_dlg_adapter('repl-stay')
#   def repl_all_from(self):                    return Find_repl_cmds.find_dlg_adapter('repl-all')

    def copy_term(self):                        return SCBs.copy_term()
    def replace_term(self):                     return SCBs.replace_term()
    def expand_sel(self):                       return SCBs.expand_sel(copy=False)
    def expand_sel_copy(self):                  return SCBs.expand_sel(copy=True)
    
    def _activate_tab(self, group, tab_ind):    return Tabs_cmds._activate_tab(     group, tab_ind)
    def _activate_last_tab(self, group):        return Tabs_cmds._activate_last_tab(group)
    def _activate_near_tab(self, gap):          return Tabs_cmds._activate_near_tab(gap)
    def move_tab(self):                         return Tabs_cmds.move_tab()
    def close_tab_from_other_group(self
                        , what_grp='next'):     return Tabs_cmds.close_tab_from_other_group(what_grp)
    def _activate_tab_other_group(self
        , what_tab='next', what_grp='next'):    return Tabs_cmds._activate_tab_other_group(what_tab, what_grp)

    def go_back_tab(self):
        if app.app_api_version()<'1.0.253':
            return app.msg_status(NEED_UPDATE)
        eds         = [app.Editor(h) for h in app.ed_handles()]     # Native order
        ed_tats     = [(ed_, ed_.get_prop(app.PROP_ACTIVATION_TIME, '')) for ed_ in eds]
        ed_tats     = [(at, ed_) for (ed_, at) in ed_tats if at]    # Only activated
        if len(ed_tats)<2:
            return app.msg_status(_('No yet other activated tab'))
        ed_tats.sort(reverse=True, key=lambda ae:ae[0])
        ed_back     = ed_tats[1][1]
        ed_back.focus()
       #def go_back_tab

    def go_back_dlg(self):
        if app.app_api_version()<'1.0.253':
            return app.msg_status(NEED_UPDATE)
#       scam    = app.app_proc(app.PROC_GET_KEYSTATE, '')
        if 'c' not in app.app_proc(app.PROC_GET_KEYSTATE, ''):          # User already is released Ctrl
            return self.go_back_tab()
        cfg_keys= get_plugcmd_hotkeys('go_back_dlg')
        pass;                  #log('ok scam,cfg_keys={}',(scam,cfg_keys))
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
#       eds         = eds if ed in eds else [ed]+eds
        eds         = eds if eds else [ed]
        eds_hist    = [(ed_, ed_.get_prop(app.PROP_TAB_ID, '')
                           , ed_.get_prop(app.PROP_TAB_TITLE) 
                           , ed_.get_filename()
                       ) for ed_ in eds]
        pass;                  #log('eds_hist={}',(eds_hist))
        start_sel   = min(1, len(eds_hist)-1)
        pass;                  #log('start_sel,len(eds_hist)={}',(start_sel,len(eds_hist)))
        ed_back     = eds_hist[start_sel][0]
        panel_to    = None
        start_pnls  = get_hist('switcher.start_panel', 'Code tree')

        ag_hist     = None
        def do_show(idd, idc, data=None):
            if 'c' not in app.app_proc(app.PROC_GET_KEYSTATE, ''):
                ag_hist.hide()
            app.timer_proc(app.TIMER_START_ONE
                          ,lambda tag: ag_hist.hide() 
                                            if 'c' not in app.app_proc(app.PROC_GET_KEYSTATE, '') 
                                            else 0
                          ,200)
           #def do_show
        
        def do_key_up(idd, idc, data=None):
            scam    = data if data is not None else app.app_proc(app.PROC_GET_KEYSTATE, '')
            if 'c' not in scam:
                ag_hist.hide()
           #def do_key_up
        
        def do_key_down(idd, idc, data=None):
            nonlocal ed_back, panel_to
            scam    = data if data is not None else app.app_proc(app.PROC_GET_KEYSTATE, '')
            pass;              #log('scam={}',(scam))
            k2K     = d(s='Shift+', c='Ctrl+', a='Alt+')
            hotkey  = ''.join(k2K[k] for k in scam) + chr(idc)
            pass;              #log('idc,hotkey,cfg_keys={}',(idc,hotkey,cfg_keys))
            to_othr = False
            sel_to  = ''
            if 0:pass
            elif idc==VK_ENTER:                             ag_hist.hide()
            elif idc==VK_ESCAPE:    panel_to=ed_back=None;  ag_hist.hide()
            
            elif idc in (VK_LEFT, VK_RIGHT):to_othr = True
            
            elif idc==VK_DOWN:              sel_to  = 'next'
            elif idc==VK_UP:                sel_to  = 'prev'
            elif idc==VK_TAB and scam== 'c':sel_to  = 'next'
            elif idc==VK_TAB and scam=='sc':sel_to  = 'prev'
            elif hotkey in cfg_keys:        sel_to  = 'next'
            else:   return 
            
            fid = ag_hist.fattr('fid')
            if to_othr:
                fid = 'pnls' if fid=='tabs' else 'tabs'
                ag_hist._update_on_call(d(
                    form=d(fid=fid)
                ,   ctrls=[('tabs',d(color=act_clr if fid=='tabs' else pss_clr))
                          ,('pnls',d(color=act_clr if fid=='pnls' else pss_clr ))
                          ]
                ))
                ed_back     = None if fid=='pnls' else eds_hist[ag_hist.cval('tabs')][0]
                panel_to    = None if fid=='tabs' else panels[  ag_hist.cval('pnls')]
            
            pass;              #log('sel_to={}',(sel_to))
            if sel_to:
                ed_back     = None
                panel_to    = None
                shft        = 1 if sel_to=='next' else -1
                if fid=='tabs':
                    sel = (ag_hist.cval('tabs') + shft) % len(eds_hist)
                    ed_back     = eds_hist[sel][0]
                    pass;      #log('sel={}',(ag_hist.cval('tabs'), sel))
                    ag_hist._update_on_call(d(vals=d(tabs=sel)))
                if fid=='pnls':
                    sel = (ag_hist.cval('pnls') + shft) % len(panels)
                    panel_to    = panels[sel]
                    if not panel_to[0]:
                        sel = (sel              + shft) % len(panels)
                        panel_to= panels[sel]
                    pass;      #log('sel={}',(ag_hist.cval('pnls'), sel))
                    ag_hist._update_on_call(d(vals=d(pnls=sel)))
            
            return False
           #def do_key_down
        
        def do_select(aid, ag, data=''):
            nonlocal ed_back, panel_to
            sel     = ag_hist.cval(aid)
            pass;              #log('sel={}',(sel))
            if aid=='tabs':
                ed_back = eds_hist[sel][0]
                panel_to= None
            if aid=='pnls':
                ed_back = None
                panel_to= panels[sel]
            return []
        
        def do_dclk(aid, ag, data=''):
            do_select(aid, ag)
            if aid=='pnls' and not panel_to[0]:
                return []   # Ignore
            return None     # Close dlg
           #def do_dclk
        
        panls       = [(pn if pn else '—'*100) for act,pn in panels]
        items       = [ed_tit for (ed_, ed_tid, ed_tit, ed_fn) in eds_hist]
        if 'c' not in app.app_proc(app.PROC_GET_KEYSTATE, ''):          # User already is released Ctrl
            return self.go_back_tab()
        ag_hist     = DlgAgent(
            form    =dict(cap=_('Switcher'), w=350, h=300
                         ,on_show       =do_show
                         ,on_key_down   =do_key_down
                         ,on_key_up     =do_key_up)
        ,   ctrls   =[0
                     ,('tabs',d(tp='lbx',items=items   ,ali=ALI_CL          ,color=act_clr  ,call=do_select ,on_click_dbl=do_dclk ,on_click=do_dclk   ))
                     ,('pnls',d(tp='lbx',items=panls   ,ali=ALI_RT  ,w=110  ,color=pss_clr  ,call=do_select ,on_click_dbl=do_dclk ,on_click=do_dclk   ))
                    ][1:]
        ,   fid     ='tabs'
        ,   vals    = d(tabs=start_sel
                       ,pnls=panls.index(start_pnls) if start_pnls in panls else 0)
                              #,options={'gen_repro_to_file':'repro_dlg_find_tree_node.py'}
        )
        if 'c' not in app.app_proc(app.PROC_GET_KEYSTATE, ''):          # User already is released Ctrl
            return self.go_back_tab()
        ag_hist.show()
        if ed_back:
            ed_back.focus()
        elif panel_to and panel_to[0]:
            set_hist('switcher.start_panel', panel_to[1])
            app.app_proc(*(panel_to[0]))
       #def go_back_dlg
    
    def scroll_to(self, place):                             return Jumps_cmds.scroll_to(place)
    def jump_to_matching_bracket(self):                     return Jumps_cmds.jump_to_matching_bracket()
    def jump_to_status_line(self, status, nx_pr, bgn_end):  return Jumps_cmds.jump_to_status_line(status, nx_pr, bgn_end)
    def jump_to_line_by_cb(self):                           return Jumps_cmds.jump_to_line_by_cb()
    def jump_ccsc(self, drct, sel):                         return Jumps_cmds.jump_ccsc(drct, sel)
    def dlg_bms_in_tab(self):                               return Jumps_cmds.dlg_bms_in_tab()
    def dlg_bms_in_tabs(self, what='a'):                    return Jumps_cmds.dlg_bms_in_tabs(what)
    def jump_staple(self, what='end'):                      return Jumps_cmds.jump_staple(what)
    
    def go_prgph(self, what):                               return Prgph_cmds.go_prgph(what)
    def align_prgph(self, how):                             return Prgph_cmds.align_prgph(how)
   #class Command


def fnd_mtch_char(ed4find, c_opn, c_cls, line, col, row, to_end):
    """ Find paired char c_opn from (col, row) in dir to_end and
            skip inside pair (c_opn, c_cls)
    """
    assert line     ==ed4find.get_text_line(row)
#   assert line[col]==c_opn
    pass;                      #LOG and log('c_opn, c_cls, line[col-1:col+2], col, row, to_end={}',(c_opn, c_cls, line[col-1:col+2], col, row, to_end))
    cnt = 1
    while True:
        for pos in (range(col, len(line)) if to_end else
                    range(col, -1, -1)):
            c = line[pos]
            if False:
                pass
            elif c == c_opn:
                cnt = cnt + 1
            elif c == c_cls:
                cnt = cnt - 1
            else:
                continue  # for pos
            pass;              #LOG and log('line, pos, c, cnt={}', (line, pos, c, cnt))
            if 0 == cnt:
                # Found!
                col = pos
                break#for pos
           #for pos
        if 0 == cnt:
            break#while
        if to_end:
            row = row + 1
            if row == ed4find.get_line_count():
                pass;          #LOG and log('not found')
                break#while
            line = ed4find.get_text_line(row)
            col = 0
        else:
            if row == 0:
                pass;          #LOG and log('not found')
                break#while
            row = row - 1
            line = ed4find.get_text_line(row)
            col = len(line) - 1
       #while
    return (c_opn, c_cls, col, row) if cnt == 0 else (c_opn, c_cls, -1, -1)
   #def fnd_mtch_char
#NOTE: mcth
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
    c_opn,  \
    c_cls,  \
    col,row = fnd_mtch_char(ed4find, c_opn, c_cls, line, col, row, to_end)
    return c_opn, c_cls, col, row
#   return (c_opn, c_cls, col, row) if cnt==0 else (c_opn, c_cls, -1, -1)
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

#######################################
if __name__ == '__main__' :     # Tests
    pass;                      #log('test')
#   Prgph_cmds.go_prgph('bgn')
#   Prgph_cmds.go_prgph('end')
#   Prgph_cmds.go_prgph('nxt')
#   Prgph_cmds.go_prgph('prv')
#   Prgph_cmds.align_prgph('l')

'''
ToDo
[+][kv-kv][20nov15] Вставить строку с отступом под/над текущей
[+][kv-kv][20nov15] Activate tab #1, #2, ..., #9 Activate tab on 2nd group #1, #2, ..., #9
[+][kv-kv][20nov15] Paste from clipboard, to 1st column: paste_to_1st_col
[?][kv-kv][20nov15] Paste from clipboard, to 1st column for m-carets
[+][kv-kv][20nov15] Find string from clipboard - next/prev: find_cb_string_next
[+][kv-kv][20nov15] Jump to matching bracket: jump_to_matching_bracket
[+][kv-kv][20nov15] CopyTerm, ReplaceTerm
[-][kv-kv][20nov15] Comment/uncomment before cur term (or fix col?)
[+][kv-kv][24nov15] Wrap for "Find string from clipboard"
[+][kv-kv][25nov15] Replace all as selected to cb-string: replace_all_sel_to_cb
[+][kv-kv][25nov15] Open selected file: open_selected
[+][kv-kv][25nov15] Catch on_console_nav
[+][kv-kv][26nov15] Scroll on_console_nav, Find*
[+][at-kv][09dec15] Refactor: find_pair
[+][kv-kv][15dec15] Find cb-string via cmd_FinderAction (for use next/prev after)
'''
