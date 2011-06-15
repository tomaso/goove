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

/*
    var subcluster_store = Ext.create('Ext.data.Store', {
        model: 'Subcluster',
        proxy: {
            type: 'ajax',
            url: '/trqlive/dynamic/subclusters_list/',
        },
        autoLoad: true
    });
*/
    var subcluster_stores = {};

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

    var tabs_nodes = {};


    var tp_store = Ext.create('Ext.data.TreeStore', {
        root: {
            expanded: true,
            text: "root",
            user: "",
            status: "",
            children: []

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
            itemclick: function (view, rec, item, index, eventObj) {
                var mp = Ext.getCmp('main-panel');
                mp.removeAll();
                if (rec.get('text') == 'Nodes') {
                    Ext.Array.each(tabs_nodes[rec.parentNode.get('text')], function (tab) {
                        console.info(tab);
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
        Ext.Array.each(records, function(bs) {
            root.appendChild({
                text: bs.get('name'),
                expanded: true,
                children: [{
                    text: "Queues",
                    leaf: true,
                    id: "queues_"+bs.get('name')
                }, {
                    text: "Nodes",
                    leaf: true,
                    id: "nodes_"+bs.get('name')
                }, {
                    text: "Users",
                    leaf: true,
                    id: "users_"+bs.get('name')
                }]
            });
            subcluster_stores[bs.get('name')] = Ext.create('Ext.data.Store', {
                model: 'Subcluster',
                proxy: {
                    type: 'ajax',
                    url: '/trqlive/dynamic/subclusters_list/'+bs.get('name')+'/',
                },
                autoLoad: true,
            });
            tabs_nodes[bs.get('name')] = [{
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
                            subcluster_stores[bs.get('name')].each(function (sc) {
                                itm = Ext.create('Ext.org.NodesView');
                                itm.store = Ext.create('Ext.data.Store', {
                                    model: 'Node',
                                    proxy: {
                                        type: 'ajax',
                                        url: '/trqlive/dynamic/nodes_overview/' + sc.get('name') + '/'
                                    },
                                    autoLoad: true,
                                });
                                thistab.add({
                                    id: sc.get('name'),
                                    xtype: 'panel',
                                    title: sc.get('name'),
                                    //flex: 1,
                                    width: 100,
                                    items: itm
                                }
                                );
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
        });
        console.info("subcluster_stores:");
        console.info(subcluster_stores);
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
