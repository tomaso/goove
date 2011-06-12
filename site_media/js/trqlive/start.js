Ext.onReady(function () {
/*
 * MODELS
 */
    Ext.define('Node', {
        extend: 'Ext.data.Model',
        fields: [{
            name: 'name',
            type: 'string'
        }, {
            name: 'state',
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

/*
 * STORES
 */
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
        itemSelector: 'span.node_overview',
        cls: 'x-node-overview',

        tpl: ['<tpl for=".">', '<div id=overview_{name}" class="node_overview {state}">', '</div>', '</tpl>']
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
                                url: '/trqlive/dynamic/nodes_overview/'
                            },
                            autoLoad: false,
                        });

                        itm.store.proxy.url = '/trqlive/dynamic/nodes_overview/' + sc.get('name') + '/';
                        itm.on('render', function (view) {
                            console.info("In render function");
                            view.tip = Ext.create('Ext.tip.ToolTip', {
                                // The overall target element.
                                target: view.el,
                                // Each grid row causes its own seperate show and hide.
                                delegate: view.itemSelector,
                                // Moving within the row should not hide the tip.
                                trackMouse: true,
                                // Render immediately so that tip.body can be referenced prior to the first show.
                                renderTo: Ext.getBody(),
                                listeners: {
                                    beforeshow: function updateTipBody(tip) {
                                        console.info(tip);
                                    }
                                }
                            });
                        });
                        //console.info(itm.store.proxy.url);
                        thistab.add({
                            id: sc.get('name'),
                            xtype: 'panel',
                            title: sc.get('name'),
                            //flex: 1,
                            width: 175,
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
                        tab.items.get(0).store.load();
                        
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

    var store = Ext.create('Ext.data.TreeStore', {
        root: {
            expanded: true,
            text: "",
            user: "",
            status: "",
            children: [{
                text: "torque.farm.particle.cz",
                expanded: true,
                children: [{
                    text: "Queues",
                    leaf: true,
                    id: "queues_torque.farm.particle.cz"
                }, {
                    text: "Nodes",
                    leaf: true,
                    id: "nodes_torque.farm.particle.cz"
                }, {
                    text: "Users",
                    leaf: true,
                    id: "users_torque.farm.particle.cz"
                }],
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
        store: store
        // could use a TreePanel or AccordionLayout for navigational items
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
/*    tooltips = [{
                    target: 'overview_salix01',
                    html: 'salix01 tooltip'
                    }
                    ];

                    Ext.each(tooltips, function(config) {
                    Ext.create('Ext.tip.ToolTip', config);
                    });
                    */
    //      console.info(tp.store.tree.root);
    //Ext.QuickTips.init();

}

); //end onReady


// vi:sw=4:ts=4:et
