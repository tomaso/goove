Ext.onReady(function () {

Ext.Loader.setConfig({enabled: true});
Ext.Loader.setPath('Ext.ux', '/site_media/js/ext/examples/ux');

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
    
    Ext.define('NodeOverview', {
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

    // TODO: filter for properties
    Ext.define('NodeProperty', {
    });

    Ext.define('NodeForList', {
        extend: 'Ext.data.Model',
        fields: [{
            name: 'name',
            type: 'string'
        }, {
            name: 'state',
            type: 'string'
        }, {
            name: 'properties',
            type: 'string'
        }, {
            name: 'subcluster',
            type: 'string'
        }]
    });

    Ext.define('QueueForList', {
        extend: 'Ext.data.Model',
        fields: [{
            name: 'name',
            type: 'string'
        }, {
            name: 'Q',
            type: 'number'
        }, {
            name: 'W',
            type: 'number'
        }, {
            name: 'R',
            type: 'number'
        }, {
            name: 'started',
            type: 'string'
        }, {
            name: 'enabled',
            type: 'string'
        }, {
            name: 'queue_type',
            type: 'string'
        }, {
            name: 'max_running',
            type: 'number'
        }, {
            name: 'total_jobs',
            type: 'number'
        }]
    });

    Ext.define('JobForList', {
        extend: 'Ext.data.Model',
        fields: [{
            name: 'jobid',
            type: 'string'
        }, {
            name: 'job_name',
            type: 'string'
        }, {
            name: 'queue',
            type: 'string'
        }, {
            name: 'job_state',
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
            url: '/trqacc/api/batchservers_list/',
        },
        autoLoad: true
    });

    var subcluster_stores = {};


/*
 * VIEWS
 */
    Ext.define('Ext.org.NodesView', {
        extend: 'Ext.view.View',
        alias: 'widget.nodesview',
        requires: ['Ext.data.Store', 'Ext.ux.grid.FiltersFeature'],
        itemSelector: 'div.node_overview',
        cls: 'x-node-overview',

        tpl: ['<tpl for=".">', '<div data-qtitle="{shortname}" data-qtip="{ttiphtml}" id="overview_id_{name}" class="node_overview {state}">', '</div>', '</tpl>'],

        listeners: {
            itemclick: function (view, rec, item, index, eventObj) {
                tip = Ext.tip.QuickTipManager.getQuickTip();
                console.info(tip);
                tip.hide();
                Ext.create('Ext.panel.Panel', {
                    floating: true,
                    closable: true,
                    alignTo: item,
                    title: tip.title,
                    html: tip.body.dom.innerHTML,
                    autoRender: true,
                    autoShow: true,
                    width: 100,
                    resizable: true,
                    draggable: {
                        insertProxy: false,

                        onDrag : function(e){
                            var pel = this.proxy.getEl();
                            this.x = pel.getLeft(true);
                            this.y = pel.getTop(true);

                            var s = this.panel.getEl().shadow;
                            if (s) {
                                s.realign(this.x, this.y, pel.getWidth(), pel.getHeight());
                            }
                        },

                        endDrag : function(e){
                            this.panel.setPosition(this.x, this.y);
                        }
                    },
                    layout: 'fit'
                }).setPosition(tip.x,tip.y,false);
            }
        }
    });

    var tabs_queues = {};
    var tabs_nodes = {};
    var tabs_users = {};
    var tabs_jobs = {};


    var maintree_store = Ext.create('Ext.data.TreeStore', {
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
                if (rec.get('text') == 'Queues') {
                    Ext.Array.each(tabs_queues[rec.parentNode.get('text')], function (tab) {
                        mp.add(tab);
                    });
                }
                if (rec.get('text') == 'Nodes') {
                    Ext.Array.each(tabs_nodes[rec.parentNode.get('text')], function (tab) {
                        mp.add(tab);
                    });
                }
                if (rec.get('text') == 'Users') {
                    Ext.Array.each(tabs_users[rec.parentNode.get('text')], function (tab) {
                        mp.add(tab);
                    });
                }
                if (rec.get('text') == 'Jobs') {
                    Ext.Array.each(tabs_jobs[rec.parentNode.get('text')], function (tab) {
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
        store: maintree_store
        // could use a TreePanel or AccordionLayout for navigational items
    });

    var node_filters = {
        ftype: 'filters',
        encode: false,
        local: true,
        filters: [{
            type: 'list',
            dataIndex: 'state',
            options: ['free', 'job-exclusive', 'down', 'offline']
        }]
    };


    batchserver_store.on('load', function (store, records, successful) {
        var root = maintree_store.getRootNode();
        Ext.Array.each(records, function(bs) {
            // Create stores for node lists
            Ext.create('Ext.data.Store', {
                storeId: 'store_nodes_list_'+bs.get('name'),
                model: 'NodeForList',
                groupField: 'subcluster',
                proxy: {
                    type: 'ajax',
                    url: '/trqacc/api/nodes_list/' + bs.get('name') + '/'
                },
                autoLoad: false
            });
            // Create stores for queue lists
            Ext.create('Ext.data.Store', {
                storeId: 'store_queues_list_'+bs.get('name'),
                model: 'QueueForList',
                proxy: {
                    type: 'ajax',
                    url: '/trqacc/api/queues_list/' + bs.get('name') + '/'
                },
                autoLoad: false
            });
            // Create stores for queue lists
            Ext.create('Ext.data.Store', {
                storeId: 'store_jobs_list_'+bs.get('name'),
                model: 'JobForList',
                proxy: {
                    type: 'ajax',
                    url: '/trqacc/api/jobs_list/' + bs.get('name') + '/'
                },
                autoLoad: false
            });

            // Fill the left tree 
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
                }, {
                    text: "Jobs",
                    leaf: true,
                    id: "jobs_"+bs.get('name')
                }]
            });
            subcluster_stores[bs.get('name')] = Ext.create('Ext.data.Store', {
                model: 'Subcluster',
                proxy: {
                    type: 'ajax',
                    url: '/trqacc/api/subclusters_list/'+bs.get('name')+'/',
                },
                autoLoad: true
            });
            tabs_queues[bs.get('name')] = [{
                title: "List",
                id: "queues_list_"+bs.get('name'),
                xtype: "gridpanel",
                selType: 'cellmodel',
                features: [{ftype:'grouping'}],
                columns: [
                    {header: 'Name',  dataIndex: 'name'},
                    {header: 'Total jobs', dataIndex: 'total_jobs', align: 'right'},
                    {header: 'Queued',  dataIndex: 'Q', align: 'right'},
                    {header: 'Waiting',  dataIndex: 'W', align: 'right'},
                    {header: 'Running',  dataIndex: 'R', align: 'right'},
                    {header: 'Max. running', dataIndex: 'max_running', align: 'right'},
                    {header: 'Started',  dataIndex: 'started', align: 'center'},
                    {header: 'Enabled', dataIndex: 'enabled', align: 'center'},
                    {header: 'Queue type', dataIndex: 'queue_type', align: 'center'}
                ],
                store: Ext.data.StoreManager.lookup('store_queues_list_'+bs.get('name')),
                listeners: {
                    show: function(thistab) {
                        thistab.store.load()
                    }
                }
            },{
                title: "Graphs",
                id: "queues_graphs_"+bs.get('name')
            }];
            tabs_nodes[bs.get('name')] = [{
                title: "Overview",
                id: "nodes_overview_"+bs.get('name'),
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
                                    model: 'NodeOverview',
                                    proxy: {
                                        type: 'ajax',
                                        url: '/trqacc/api/nodes_overview/'+bs.get('name')+'/' + sc.get('name') + '/'
                                    },
                                    autoLoad: true
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
                id: "nodes_list" + bs.get('name'),
                xtype: "gridpanel",
                features: [{ftype:'grouping'}, node_filters],
                columns: [
                    {header: 'Name',  dataIndex: 'name', flex:1},
                    {header: 'Subcluster',  dataIndex: 'subcluster', flex:1, hidden: true},
                    {header: 'State', dataIndex: 'state', flex: 1},
                    {header: 'Properties', dataIndex: 'properties', flex:2}
                ],
                store: Ext.data.StoreManager.lookup('store_nodes_list_'+bs.get('name')),
                listeners: {
                    show: function(thistab) {
                        thistab.store.load()
                    }
                }
                
            }];
            tabs_users[bs.get('name')] = [{
                title: "Active users",
                id: "users_list_"+bs.get('name')
            }];
            tabs_jobs[bs.get('name')] = [{
                title: "Current jobs list",
                id: "jobs_list_"+bs.get('name'),
                xtype: "gridpanel",
                columns: [
                    {header: 'JobId',  dataIndex: 'jobid', flex:1},
                    {header: 'Job Name', dataIndex: 'job_name', flex:1},
                    {header: 'Queue', dataIndex: 'queue', flex:1},
                    {header: 'Job state', dataIndex: 'job_state', flex:1}
                ],
                store: Ext.data.StoreManager.lookup('store_jobs_list_'+bs.get('name')),
                listeners: {
                    show: function(thistab) {
                        console.info(thistab.store.count())
                        if(thistab.store.count()==0) {
                            thistab.store.load()
                        }
                    }
                }
            }];
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
