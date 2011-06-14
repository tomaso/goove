Ext.onReady(function () {
/*
 * MODELS
 */
    Ext.define('BatchServer', {
        extend: 'Ext.data.Model',
        fields: [{
            name: 'name',
            type: 'string'
        }]
    });

    Ext.define('Subcluster', {
        extend: 'Ext.data.Model',
        fields: [{
            name: 'name',
            type: 'string'
        }]
    });
    
    Ext.define('Node', {
        extend: 'Ext.data.Model',
        fields: [{
            name: 'name',
            type: 'string'
        }, {
            name: 'shortname',
            type: 'string'
        }, {
            name: 'state',
            type: 'string'
        }, {
            name: 'ttiphtml',
            type: 'string'
        }]
    });


/*
 * STORES
 */
    var batchserver_store = Ext.create('Ext.data.Store', {
        model: 'BatchServer',
        proxy: {
            type: 'ajax',
            url: '/trqlive/dynamic/batchservers_list/',
        },
        autoLoad: true
    });

    var subcluster_store = Ext.create('Ext.data.Store', {
        model: 'Subcluster',
        proxy: {
            type: 'ajax',
            url: '/trqlive/dynamic/subclusters_list/',
        },
        autoLoad: true
    });

    // See API docs for loading nested data - Ext.data.reader.Reader
    var node_store = Ext.create('Ext.data.Store', {
        model: 'Node',
        proxy: {
            type: 'ajax',
            url: '/trqlive/dynamic/nodes_overview/'
        },
        autoLoad: false
    });

/*
 * VIEWS
 */
    Ext.define('Ext.org.NodesView', {
        extend: 'Ext.view.View',
        alias: 'widget.nodesview',
        requires: ['Ext.data.Store'],
        itemSelector: 'div.node_overview',
        cls: 'x-node-overview',

        tpl: ['<tpl for=".">', '<div data-qtitle="{shortname}" data-qtip="{ttiphtml}" id="overview_id_{name}" class="node_overview {state}">', '</div>', '</tpl>']
    });

    var tabs_nodes = [{
        title: "Overview",
        id: "nodes_overview",
        xtype: 'panel',
        autoScroll: true,
        layout: {                        
            type: 'hbox',
            align: 'stretch'
        },
        region: 'center',
        listeners: {
            activate: function(thistab) {
                if(thistab.items.getCount()==0) {
                    subcluster_store.each(function (sc) {
                        itm = Ext.create('Ext.org.NodesView');
                        itm.store = Ext.create('Ext.data.Store', {
                            model: 'Node',
                            proxy: {
                                type: 'ajax',
                                url: '/trqlive/dynamic/nodes_overview/' + sc.get('name') + '/'
                            },
                            autoLoad: true,
                        });

                        /*                        
                        itm.on('render', function (view) {
                            view.tip = Ext.create('Ext.tip.ToolTip', {
                                // The overall target element.
                                target: view.el,
                                // Each grid row causes its own seperate show and hide.
                                delegate: view.itemSelector,
                                // Moving within the row should not hide the tip.
                                trackMouse: true,
                                // Render immediately so that tip.body can be referenced prior to the first show.
                                renderTo: Ext.getBody(),
                                html: 'This is the default tooltip',
                                listeners: {
                                    beforeshow: function updateTipBody(tip) {
                                        //                                        console.info(view.getStore());
                                        //                                        var node = view.getNode(view.el);
                                        console.info(tip);
                                        console.info(tip.triggerElement);
                                        //                                        console.info(view.getRecord(tip));
                                        //                                        tip.update(view.getRecord().jobs[0]);
                                    }
                                }
                            });
                        });
                        //*/                        
                        thistab.add({
                            id: sc.get('name'),
                            xtype: 'panel',
                            title: sc.get('name'),
                            //flex: 1,
                            width: 100,
                            /*
                            items: {
                                xtype: 'nodesview'
                            }
                            */
                            items: itm
                        }
                        );
                        tab = thistab.items.get(sc.get('name'));
                        //console.info(tab.items.get(0).store.proxy);
/*                        
                        var operation = new Ext.data.Operation({
                            action: 'read',
                            sname : sc.get('name')
                        });
*/                        
//                        tab.items.get(0).store.load();
/*                        
                        console.info(itm);
                        console.info(itm.store);
                        console.info(itm.store.totalCount);
                        itm.store.each(function (n) {
                            Ext.create('Ext.tip.ToolTip', {
                                target: Ext.getCmp(n),
                                trackMouse: true,
                                html: n
                            });
                            console.info(n);
                        });
*/                        
                    });
                }
            },
            deactivate: function(thistab) {
                //console.info('deactivated');
            }
        }
    }, {
        title: "List",
        id: "nodes_list"
    }];

    var tp_store = Ext.create('Ext.data.TreeStore', {
        root: {
            expanded: true,
            text: "root",
            user: "",
            status: "",
            children: []

/*            
            }, {
                text: "service0.dorje.fzu.cz",
                expanded: false,
                children: [{
                    text: "Queues",
                    leaf: true
                }, {
                    text: "Nodes",
                    leaf: true
                }, {
                    text: "Users",
                    leaf: true
                }],
            }, {
                text: "golias.farm.particle.cz",
                expanded: false,
                children: [{
                    text: "Queues",
                    leaf: true
                }, {
                    text: "Nodes",
                    leaf: true
                }, {
                    text: "Users",
                    leaf: true
                }],
            }, {
                text: "ce2.egee.cesnet.cz",
                expanded: false,
                children: [{
                    text: "Queues",
                    leaf: true
                }, {
                    text: "Nodes",
                    leaf: true
                }, {
                    text: "Users",
                    leaf: true
                }],
            }, ]
*/            
        }
    });
    var tp = Ext.create('Ext.tree.Panel', {
        region: 'west',
        collapsible: true,
        title: 'Entities',
        width: 200,
        split: true,
        xtype: 'treepanel',
        useArrows: true,
        rootVisible: false,
        listeners: {
/*            
            afterrender: function(thispanel) {
                var root = thispanel.store.getRootNode();
                root.appendChild({
                    text: "name_",
                    expanded: true,
                    children: [{
                        text: "Queues",
                        leaf: true,
                        id: "queues_"
                    }]
                });
                console.info('listener');
                console.info(root);
                console.info(batchserver_store);
                batchserver_store.load();
                batchserver_store.each(function (bs) {
                    console.info(bs.name);
                    root.appendChild({
                        text: bs.name,
                        expanded: true,
                        children: [{
                            text: "Queues",
                            leaf: true,
                            id: "queues_"+bs.name
                        }, {
                            text: "Nodes",
                            leaf: true,
                            id: "nodes_"+bs.name
                        }, {
                            text: "Users",
                            leaf: true,
                            id: "users_"+bs.name
                        }]
                    });
                });
            },
*/            
            itemclick: function (view, rec, item, index, eventObj) {
                var mp = Ext.getCmp('main-panel');
                mp.removeAll();
                if (rec.get('text') == 'Nodes') {
                    Ext.Array.each(tabs_nodes, function (tab) {
                        mp.add(tab);
                    });
                }
/*
                                    var curtab = Ext.getCmp('tab_'+rec.get('id'));
                                    if(!curtab) {
                                    curtab = {
                                    id: 'tab_'+rec.get('id'),
                                    title: rec.get('id'),
                                    html: '<b>' + rec.get('id') + '</b>'
                                    };
                                    curtab = mp.add(curtab);
                                    }
                                    mp.setActiveTab(curtab);
                                    */
            }
        },
        store: tp_store
        // could use a TreePanel or AccordionLayout for navigational items
    });
    batchserver_store.on('load', function (store, records, successful) {
        var root = tp_store.getRootNode();
        Ext.Array.each(records, function(rec) {
            root.appendChild({
                text: rec.get('name'),
                expanded: true,
                children: [{
                    text: "Queues",
                    leaf: true,
                    id: "queues_"+rec.get('name')
                }, {
                    text: "Nodes",
                    leaf: true,
                    id: "nodes_"+rec.get('name')
                }, {
                    text: "Users",
                    leaf: true,
                    id: "users_"+rec.get('name')
                }]
            });
        });
    });
    var vp = Ext.create('Ext.container.Viewport', {
        layout: 'border',
        renderTo: Ext.getBody(),
        items: [tp,
        {
            region: 'south',
            title: 'Help',
            collapsible: true,
            split: true,
            height: 150
        }, {
            id: 'main-panel',
            region: 'center',
            xtype: 'tabpanel',
            // TabPanel itself has no title
            activeTab: 0,
            // First tab active by default
            items: [{
                id: 'overview',
                title: 'Overview',
                html: 'This page should contain welcome overview.'
            }]
        }]
    });
    Ext.tip.QuickTipManager.init();
    Ext.apply(Ext.tip.QuickTipManager.getQuickTip(), {
        minWidth: 100,
        trackMouse: false,
        showDelay: 0
    });
}

); //end onReady


// vi:sw=4:ts=4:et
