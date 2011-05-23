Ext.onReady(function() {
    var buttonClicked = function() {
        Ext.Ajax.defaultHeaders = {
            'Accept': 'application/json'
        };
        var resp = Ext.Ajax.request({
            url: '/trqlive/api/nodes/',
            method: 'GET',
            success: function(resp) {
                var item = Ext.decode(resp.responseText).data[0].name;
                var myDiv = Ext.get('myDiv');
                myDiv.update('The first item in the node list is: <br />' + item);
            },
            failure: function() {
                Ext.Msg.alert('Failed');
            },
        });

    }
    Ext.get('myButton').on('click', buttonClicked);
    Ext.get('staticcontent').remove();
});

