''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '1.7.02 2019-06-11'
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

pass;                           _log4mod = LOG_FREE  # Order log in the module

d       = dict
first_true  = lambda iterable, default=False, pred=None: next(filter(pred, iterable), default)  # 10.1.2. Itertools Recipes


def symbol_menu():
    symbol_menu_levels()
def symbol_menu_levels(levels=0):
    pass;                       log4fun=-1== 1  # Order log in the function
    if  app.app_api_version() >= '1.0.277' and \
        ed.get_prop(app.PROP_CODETREE_MODIFIED_VERSION) < ed.get_prop(app.PROP_MODIFIED_VERSION):
        ed.cmd(cmds.cmd_TreeUpdate)
    h_tree = app.app_proc(app.PROC_GET_CODETREE, '')
        
    def tree_items_to_list(props=None, id_node=0, prefix='', more_levels=1000):
        '''Get all tree nodes to "props" starting from id_node (e.g. 0)'''
        props = [] if props is None else props 
        nodes = app.tree_proc(h_tree, app.TREE_ITEM_ENUM, id_node)
        if not nodes:
            nodes = app.tree_proc(h_tree, app.TREE_ITEM_ENUM, id_node)
            if not nodes:
                return 
        for id_kid, cap in nodes:
            prop    = app.tree_proc(h_tree, app.TREE_ITEM_GET_PROPS, id_kid)
            rng     = app.tree_proc(h_tree, app.TREE_ITEM_GET_RANGE, id_kid)
            subs    = prop['sub_items']
            if rng[0]>=0:
                prop['rng'] = rng
                prop['_t']  = f('{}{}\t{}'
                                , prefix
                                , prop['text']
                                , f('{}:{}', 1+rng[1], 1+rng[3]))
                props.append(prop)
            if subs and more_levels:
                # need items with sub_items too
                tree_items_to_list(props, id_kid, prefix+' '*4, more_levels-1)
        return props
       #def tree_items_to_list
    
    old_api     = app.app_api_version() < '1.0.277'
    while True:
        props = tree_items_to_list(more_levels=(levels-1 if levels else 1000))
        if not props:
            ed.cmd(cmds.cmd_TreeUpdate)
            props = tree_items_to_list()
            if not props:
                return app.msg_status(_('No items in Code Tree'))

        items       = [p['_t'] for p in props]
        crt_row     = ed.get_carets()[0][1]
        covers      = [(p['rng'][3]-p['rng'][1], n) for n,p in enumerate(props) 
                        if p['rng'][1] <= crt_row <= p['rng'][3]]
        start_item  = min(covers)[1] if covers else 0
        res = app.dlg_menu(app.MENU_LIST+app.MENU_NO_FULLFILTER
                        , items 
                        + ([_('<Update Code Tree>')] if old_api else [])
                        + [_('              <All levels>')]
                        + [_('              <Only 1 up level>')]
                        + [_('              <Only 2 up levels>')]
                        , focused=start_item
                        , caption=_('Code Tree symbols')
                                 + f(' ({})'    , len(items))
                                 +(f(' (up {})' , levels    ) if levels else '')
                        )
        if res is None: return
        if res==len(props) and old_api:
            ed.cmd(cmds.cmd_TreeUpdate)
            continue#while
        if res==0+len(props) + (1 if old_api else 0):
            levels  = 0
            continue#while
        if res==1+len(props) + (1 if old_api else 0):
            levels  = 1
            continue#while
        if res==2+len(props) + (1 if old_api else 0):
            levels  = 2
            continue#while
        break
       #while
        
    x, y, x1, y1 = props[res]['rng']
    ed.set_caret(x, y)
    #def symbol_menu
    

def find_tree_node():
    pass;                       log4fun=-1==-1  # Order log in the function
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
        return tree_nds
       #def scan_tree
    scan_tree(0, tree_t, [])    # 0 is root
    pass;                      #log('tree_t={}',pfrm100(tree_t)) if iflog(log4fun,_log4mod) else 0
    pass;                      #log('tree_p={}',pfrm100(tree_p)) if iflog(log4fun,_log4mod) else 0
        
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
        
    def do_attr(ag, aid, data=''):
        nonlocal prev_wt
        prev_wt = ''
        return d(fid='what')
    
    def do_menu(ag, aid, data=''):
        def wnen_menu(ag, tag):
            nonlocal opts, prev_wt
            if   tag in ('prev','next'):    return do_next(ag, tag)
            if   tag in ('fpth','clos'):    prev_wt = '';   opts[tag] = not opts[tag]
            elif tag=='help':               app.msg_box(HELP_C, app.MB_OK)
            elif tag=='rest':               ed.set_caret(*ed_crts[0]);      return None
            return []
           #def wnen_menu
        
        ag.show_menu(
            [ d(    tag='help'  ,cap=_('&Help...')
            ),d(                 cap='-'
            ),d(    tag='prev'  ,cap=_('Find &previous')                                ,key='Shift+Enter'
            ),d(    tag='next'  ,cap=_('F&ind next')                                    ,key='Enter'
            ),d(                 cap='-'
            ),d(                 cap=_('&Options')  ,sub=
                [ d(tag='fpth'  ,cap=_('Show full tree path')   ,ch=opts['fpth']
                ),d(tag='clos'  ,cap=_('Close on success')      ,ch=opts['clos']
            )]),d(               cap='-'
            ),d(    tag='rest'  ,cap=_('Restore initial selection and close dialog &=') ,key='Shift+Esc'
            )]
        ,   aid
        ,   cmd4all=wnen_menu                                   # Set cmd=wnen_menu for all nodes
        )
        return d(fid='what')
       #def do_menu
    
    def do_next(ag, aid, data=''):
        if not ready_l:         return d(fid='what')
        nonlocal ready_p
        ready_n = ready_p + (-1 if aid=='prev' else 1)
        ready_n = ready_n % len(ready_l) if opts['wrap'] else max(0, min(len(ready_l)-1, ready_n), 0)
        pass;                  #log('ready_n,ready_p={}',(ready_n,ready_p)) if iflog(log4fun,_log4mod) else 0
        if ready_p == ready_n:  return d(fid='what')
        ready_p = ready_n
        ready_st()
        select_node(ready_l[ready_p][0])
        return d(fid='what')
       #def do_next
    
    def do_find(ag, aid, data=''):
        nonlocal opts, tree_p, prev_wt, ready_l, ready_p
        # What/how/where will search
        what        = ag.val('what')
        if prev_wt==what and ready_l:
            return do_next(ag, 'next')
        prev_wt  = what
        pass;                  #log('what={}',(what)) if iflog(log4fun,_log4mod) else 0
        if not what:
            ready_l, ready_p    = [], -1
            return d(fid='what')
        opts['hist']= add_to_hist(what, opts['hist'])
        opts.update(ag.vals(['reex','case','word','wrap']))
        pass;                  #log('opts={}',(opts)) if iflog(log4fun,_log4mod) else 0
        tree_sid    = app.tree_proc(ID_TREE, app.TREE_ITEM_GET_SELECTED)    # cur
        nodes       = tree_p                                                # To find from top
        if tree_sid and opts['clos']:                                       # To find from cur
            # Trick: [..,i,sid]+[j,..]   switch to   [j,..] or [j,..]+[..,i]  to search first after cur
            nids    = [nid for nid, cap, path in tree_p]
            pos     = nids.index(tree_sid)
            nodes   = tree_p[pos+1:] + (tree_p[:pos] if opts['wrap'] else [])
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
        pass;                  #log('ready_l={}',(ready_l)) if iflog(log4fun,_log4mod) else 0
        ready_p = -1    if not ready_l  else \
                  0     if not tree_sid else \
                  first_true(enumerate(ready_l), 0, (lambda n_nid_cap_ndn: n_nid_cap_ndn[1][2]>tree_ndn))[0]
        pass;                  #log('ready_p={}',(ready_p)) if iflog(log4fun,_log4mod) else 0
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
    
    def do_key_down(ag, key, data=''):
        scam    = data if data else app.app_proc(app.PROC_GET_KEYSTATE, '')
        pass;                  #log('key,data,scam={}',(key,data,scam)) if iflog(log4fun,_log4mod) else 0
        if 0:pass
        elif (scam,key)==('s',VK_ENTER):        # Shift+Enter
            ag.update(do_next(ag, 'prev'))
        elif (scam,key)==('s',VK_ESCAPE):       # Shift+Esc
            ed.set_caret(*ed_crts[0])
            return None
        else: return [] # Nothing
        return False    # Stop event
       #def do_key_down
    
    ag      = DlgAg(
        form    =dict(cap=_('Find tree node'), w=365, h=58, h_max=58
                     ,on_key_down=do_key_down
                     ,border=app.DBORDER_TOOLSIZE
#                    ,resize=True
                     )
    ,   ctrls   =[0
  ,('find',d(tp='bttn',y=0          ,x=-99      ,w=44   ,cap=''     ,sto=False  ,def_bt=T           ,on=do_find         ))  # Enter
  ,('reex',d(tp='chbt',tid='what'   ,x=5+38*0   ,w=39   ,cap='.&*'  ,hint=_('Regular expression')   ,on=do_attr         ))  # &*
  ,('case',d(tp='chbt',tid='what'   ,x=5+38*1   ,w=39   ,cap='&aA'  ,hint=_('Case sensitive')       ,on=do_attr         ))  # &a
  ,('word',d(tp='chbt',tid='what'   ,x=5+38*2   ,w=39   ,cap='"&w"' ,hint=_('Whole words')          ,on=do_attr         ))  # &w
  ,('wrap',d(tp='chbt',tid='what'   ,x=5+38*3   ,w=39   ,cap='&O'   ,hint=_('Wrapped search')       ,on=do_attr         ))  # &/
  ,('what',d(tp='cmbx',y  =5        ,x=5+38*4+5 ,w=155  ,items=opts['hist']                                     ,a='r>' ))  # 
  ,('menu',d(tp='bttn',tid='what'   ,x=320      ,w=40   ,cap='&='                                   ,on=do_menu ,a='>>' ))  # &=
  ,('stbr',d(tp='stbr'              ,x=0        ,r=365                                  ,ali=ALI_BT             ,a='r>' ))  # 
                ][1:]
    ,   fid     ='what'
    ,   vals    = {k:opts[k] for k in ('reex','case','word','wrap')}
                          #,options={'gen_repro_to_file':'repro_dlg_find_tree_node.py'}
    )
    stbr    = ag.chandle('stbr')
    app.statusbar_proc(stbr, app.STATUSBAR_ADD_CELL             , tag=1)
    app.statusbar_proc(stbr, app.STATUSBAR_SET_CELL_AUTOSTRETCH , tag=1, value=True)
    ag.show(lambda ag: set_hist('tree.find_node', upd_dict(opts, ag.vals(['reex','case','word','wrap']))))
   #def find_tree_node
   

def tree_path_to_status():
    pass;                  #log('?',())
    path_l, gap = _get_best_tree_path(ed.get_carets()[0][1])
    if not path_l:  return
    ID_TREE = app.app_proc(app.PROC_SIDEPANEL_GET_CONTROL, 'Code tree')
    if not ID_TREE: return
    id_sel  = app.tree_proc(ID_TREE, app.TREE_ITEM_GET_SELECTED)
    id_need = path_l[-1][0]
    if id_need != id_sel:
        app.tree_proc(ID_TREE, app.TREE_ITEM_SELECT, id_need)
    path    = '['+ '] / ['.join([cap.rstrip(':')[:40] for (nid,cap) in path_l]) + ']'
    return app.msg_status_alt(
        path if gap==0 else f('[{:+}] {}', -gap, path)
    , 10)
   #def tree_path_to_status
   
def set_nearest_tree_node():
    path_l, gap = _get_best_tree_path(ed.get_carets()[0][1])
    if not path_l:  return
    ID_TREE = app.app_proc(app.PROC_SIDEPANEL_GET_CONTROL, 'Code tree')
    if not ID_TREE: return
    app.tree_proc(ID_TREE, app.TREE_ITEM_SELECT, path_l[-1][0])
   #def set_nearest_tree_node
   

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
        pass;                  #log('>>id_prnt, prnt_cap, kids={}',(id_prnt, prnt_cap, len(kids) if kids else 0))
        if kids is None:
            pass;              #log('<<no kids',())
            return [], INF
        row_bfr, kid_bfr, cap_bfr = -INF, NO_ID, ''
        row_aft, kid_aft, cap_aft = +INF, NO_ID, ''
        for kid, cap in kids:
            pass;              #log('kid, cap={}',(kid, cap))
            cMin, rMin, \
            cMax, rMax  = app.tree_proc(ID_TREE, app.TREE_ITEM_GET_SYNTAX_RANGE , kid) \
                            if app.app_api_version() < '1.0.226' else \
                          app.tree_proc(ID_TREE, app.TREE_ITEM_GET_RANGE        , kid)
            pass;              #log('? kid,cap, rMin,rMax,row={}',(kid,cap, rMin,rMax,row))
            if False:pass
            elif rMin<=row<=rMax:   # Cover!
                sub_l, gap_sub  = best_path(kid, cap)
                pass;          #log('? sub_l, gap_sub={}',(sub_l, gap_sub))
                if gap_sub == 0:    # Sub-kid also covers
                    pass;      #log('+ sub_l={}',(sub_l))
                    rsp_l   = [(kid, cap)] + sub_l
                else:               # The kid is best
                    pass;      #log('0 ',())
                    rsp_l   = [(kid, cap)]
                pass;          #log('<<! rsp_l={}',(rsp_l))
                return rsp_l, 0
            elif row_bfr                  < rMax            < row:
                row_bfr, kid_bfr, cap_bfr = rMax, kid, cap
                pass;          #log('< row_bfr, kid_bfr, cap_bfr={}',(row_bfr, kid_bfr, cap_bfr))
            elif row_aft                  > rMin            > row:
                row_aft, kid_aft, cap_aft = rMin, kid, cap
                pass;          #log('> row_aft, kid_aft, cap_aft={}',(row_aft, kid_aft, cap_aft))
           #for kid
        pass;                  #log('? row_bfr, kid_bfr, cap_bfr={}',(row_bfr, kid_bfr, cap_bfr))
        pass;                  #log('? row_aft, kid_aft, cap_aft={}',(row_aft, kid_aft, cap_aft))
        pass;                  #log('? abs(row_bfr-row), abs(row_aft-row)={}',(abs(row_bfr-row), abs(row_aft-row)))
        kid_x, cap_x, gap_x = (kid_bfr, cap_bfr, row_bfr-row) \
                            if abs(row_bfr-row) <= abs(row_aft-row) else \
                              (kid_aft, cap_aft, row_aft-row)
        pass;                  #log('kid_x, cap_x, gap_x={}',(kid_x, cap_x, gap_x))
        sub_l, gap_sub  = best_path(kid_x, cap_x)
        pass;                  #log('? sub_l,gap_sub ?? gap_x={}',(sub_l, gap_sub, gap_x))
        if abs(gap_sub) <= abs(gap_x):  # Sub-kid better
            rsp_l  = [(kid_x, cap_x)] + sub_l
            pass;              #log('<<sub bt: rsp_l, gap_sub={}',(rsp_l, gap_sub))
            return rsp_l, gap_sub
        # The kid is best
        rsp_l   = [(kid_x, cap_x)]
        pass;                  #log('<<bst: rsp_l, gap_x={}',(rsp_l, gap_x))
        return rsp_l, gap_x
       #def best_path
    lst, gap= best_path(0)
    pass;                      #log('lst, gap={}',(lst, gap))
    return lst, gap
   #def _get_best_tree_path
