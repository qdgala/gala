odoo.define('web_organization_tree.Organization_Tree_Widget', function (require) {
    'use strict';
    var core = require('web.core');
    var View = require('web.View');
    var data = require('web.data');
    var Widget = require('web.Widget');
    var Model = require('web.Model');
    var pyeval = require('web.pyeval');

    var QWeb = core.qweb;
    var _lt = core._lt;
    var _t = core._t;

    var Organization_Tree_Widget = View.extend({
        template: 'Organization_Tree_Widget',
        init: function (parent, model, domain, context, options) {
            this._super(parent);
            this.parent = parent;
            this.svgGroup;
            this.tree;
            this.root;
            this.zoomListener;
            this.draggingNode = null;
            this.viewerHeight;
            this.viewerWidth;
            this.maxLabelLength = 0;

            this.domain = domain;
            this.context = context;
            this.defaults = {};
            this.i = 0;

            this.ds_tree_model = new data.DataSetSearch(this, model.model);
            //this.ds_tree_model_method = options.action.params.tree_method || 'get_organization_tree';
            this.ds_tree_model_method = 'get_organization_tree';

            this.open_action;


        },

        start: function () {
            this._super.apply(this);
            this.search_employee();
        },


        search_employee: function (search) {
            var domain = this.domain || [];
            var context = this.context || {};
            return this.ds_tree_model.call(this.ds_tree_model_method, [[], domain, context]).then(this.proxy('tree_render'));
        },

        tree_render: function (result) {
            var self = this;
            this.open_action = result[1];
            this.main_tree(result[0]);
        },

        main_tree: function (data) {
            var self = this;
            //员工 ['id', 'parent_id', 'name', 'job_id', 'department_id', 'company_id']

            if (data.length == 1) {
                comp = data[0]
            } else {
                var comp = {}
                comp = {name: '组织结构图', 'id': 'o_1001'};
                comp['children'] = data;
            }
            self.render_tree(comp);
        },

        render_tree: function (treeData) {

            var self = this;

            //treeData = this.get_test_date();
            // Calculate total nodes, max label length
            var totalNodes = 0;
            this.maxLabelLength = 0;
            // variables for drag/drop
            this.selectedNode = null;
            this.draggingNode = null;
            // panning variables
            var panSpeed = 200;
            this.panBoundary = 20; // Within 20px from edges will pan when dragging.
            // Misc. variables
            this.i = 0;
            this.duration = 750;
            //var root;

            // size of the diagram 图像区域大小
            this.viewerWidth = $(document).width(); //this.$el.width(); //$(document).width()-221;
            this.viewerHeight = $(document).height() - 26; //$(document).height()-96;

            //定义一个Tree对象,树状图布局
            this.tree = d3.layout.tree()
                .size([this.viewerHeight, this.viewerWidth]);

            // define a d3 diagonal projection for use by the node paths later on.
            // 对角线生成器,projection() 是一个点变换器，默认是 [ d.x , d.y ]，即保持原坐标不变，如果写成 [ d.y , d.x ] ，即是说对任意输入的顶点，都交换 x 和 y 坐标
            this.diagonal = d3.svg.diagonal()
                .projection(function (d) {
                    return [d.y, d.x];
                });

            // Call visit function to establish maxLabelLength
            this.visit(treeData, function (d) {
                totalNodes++;
                self.maxLabelLength = Math.max(d.name.length, self.maxLabelLength);

            }, function (d) {
                return d.children && d.children.length > 0 ? d.children : null;
            });

            // Sort the tree initially incase the JSON isn't in a sorted order.
            // 排序树最初装进箱JSON并不是按一定的顺序排列。
            this.sortTree();


            // define the zoomListener which calls the zoom function on the "zoom" event constrained within the scaleExtents
            // 定义缩放监听
            this.zoomListener = d3.behavior.zoom().scaleExtent([0.1, 3]).on("zoom", function () {
                self.zoom()
            });
            // define the baseSvg, attaching a class for styling and the zoomListener
            // 定义baseSvg变量,附加样式的类和缩放监听
            this.baseSvg = d3.select("#tree-container").append("svg")  //
                .attr("width", this.viewerWidth)
                .attr("height", this.viewerHeight)
                //.attr("class", "overlay")
                .call(this.zoomListener);  //缩放监听


            // Append a group which holds all nodes and which the zoom Listener can act upon.
            // 在基本Svg表
            this.svgGroup = this.baseSvg.append("g");  //var baseSvg = d3.select("#tree-container").append("svg")

            // Define the root  定义顶点
            this.root = treeData;
            this.root.x0 = 100 //this.viewerHeight / 2;
            this.root.y0 = 0;

            this.dragListener = d3.behavior.drag()
                .on("dragstart", function (d) {
                    if (d == self.root) {
                        return;
                    }
                    self.dragStarted = true;
                    var nodes = self.tree.nodes(d);
                    d3.event.sourceEvent.stopPropagation();
                })
                .on("drag", function (d) {
                    self.on_drag(d, this)
                })
                .on("dragend", function (d) {
                    if (d == self.root) {
                        return;
                    }
                    var domNode = this;
                    if (self.selectedNode) {
                        var index = self.draggingNode.parent.children.indexOf(self.draggingNode);
                        if (index > -1) {
                            self.draggingNode.parent.children.splice(index, 1);
                        }
                        if (typeof self.selectedNode.children !== 'undefined' || typeof self.selectedNode._children !== 'undefined') {
                            if (typeof self.selectedNode.children !== 'undefined') {
                                self.selectedNode.children.push(self.draggingNode);
                            } else {
                                self.selectedNode._children.push(self.draggingNode);
                            }
                        } else {
                            self.selectedNode.children = [];
                            self.selectedNode.children.push(self.draggingNode);
                        }
                        self.expand(self.selectedNode);
                        self.sortTree();
                        self.endDrag(domNode, self.tree);
                    } else {
                        self.endDrag(domNode, self.tree);
                    }
                })


            // Layout the tree initially and center on the root node.
            this.update(this.root);
            this.firstShowNode(this.root);


        },


        // Define the zoom function for the zoomable tree
        // 为可缩放的树定义的变焦缩放功能
        zoom: function () {
            // var svgGroup = baseSvg.append("g");  //var baseSvg = d3.select("#tree-container").append("svg")
            this.svgGroup.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
        },

        // sort the tree according to the node names
        // 根据节点名称排序树
        sortTree: function () {
            this.tree.sort(function (a, b) {
                return b.name.toLowerCase() < a.name.toLowerCase() ? 1 : -1;
            });
        },

        // A recursive helper function for performing some setup by walking through all nodes

        visit: function (parent, visitFn, childrenFn) {
            if (!parent) return;

            visitFn(parent);

            var children = childrenFn(parent);
            if (children) {
                var count = children.length;
                for (var i = 0; i < count; i++) {
                    this.visit(children[i], visitFn, childrenFn);
                }
            }
        },


        // Helper functions for collapsing and expanding nodes.
        // 折叠和展开节点的帮助函数

        collapse: function (d) {  //折叠
            if (d.children) {
                d._children = d.children;
                d._children.forEach(collapse);
                d.children = null;
            }
        },

        expand: function (d) {  //展开
            if (d._children) {
                d.children = d._children;
                d.children.forEach(expand);
                d._children = null;
            }
        },

        //////////tuo
        on_drag: function (d, obj) {
            var self = this;
            var panTimer;
            if (d == self.root) {
                return;
            }
            if (self.dragStarted) {
                var domNode = obj;
                self.initiateDrag(d, domNode, self.tree);
            }
            var relCoords = d3.mouse($('svg').get(0));
            if (relCoords[0] < self.panBoundary) {
                panTimer = true;
                self.pan(obj, 'left');
            } else if (relCoords[0] > ($('svg').width() - self.panBoundary)) {

                panTimer = true;
                self.pan(obj, 'right');
            } else if (relCoords[1] < self.panBoundary) {
                panTimer = true;
                self.pan(obj, 'up');
            } else if (relCoords[1] > ($('svg').height() - self.panBoundary)) {
                panTimer = true;
                self.pan(obj, 'down');
            } else {
                try {
                    clearTimeout(panTimer);
                } catch (e) {

                }
            }
            d.x0 += d3.event.dy;
            d.y0 += d3.event.dx;
            var node = d3.select(obj);
            node.attr("transform", "translate(" + d.y0 + "," + d.x0 + ")");
            self.updateTempConnector();
        },

        //初始化拖拽
        initiateDrag: function (d, domNode) {
            var self = this
            self.draggingNode = d;
            d3.select(domNode).select('.ghostCircle').attr('pointer-events', 'none');
            d3.selectAll('.ghostCircle').attr('class', 'ghostCircle show');  //对所有用于拖放的红色半透明大圆圈设置两个样式类,show这个样式类是显示出来
            d3.select(domNode).attr('class', 'node activeDrag');

            // var svgGroup = baseSvg.append("g");  //var baseSvg = d3.select("#tree-container").append("svg")
            this.svgGroup.selectAll("g.node").sort(function (a, b) { // select the parent and sort the path's
                if (a.id != self.draggingNode.id) return 1; // a is not the hovered element, send "a" to the back
                else return -1; // a is the hovered element, bring "a" to the front
            });
            // if nodes has children, remove the links and nodes
            // 如果拖拽的节点有子节点,将删除连接线和所有拖拽节点的子节点
            if (nodes.length > 1) {
                // remove link paths
                var links = this.tree.links(nodes);  //获取拖拽节点的所有连接线DOM,这些连接线是当前节点和它的子节点的连接线集合
                var nodeaths = this.svgGroup.selectAll("path.link")
                    .data(links, function (d) {
                        return d.target.id;
                    }).remove();  //找到这些连接线然后删除,因为要换一个父节点,所以要先把连接线先去掉
                // remove child nodes
                var nodesExit = this.svgGroup.selectAll("g.node")  //获取所有拖拽节点的DOM
                    .data(nodes, function (d) {
                        return d.id;
                    }).filter(function (d, i) {  //对找到的节点进行筛选
                        if (d.id == self.draggingNode.id) {  // draggingNode = d;  对于拖拽的当前节点除外
                            return false;
                        }
                        return true;
                    }).remove(); //删除节点DOM
            }

            // remove parent link  移除父链接,这是当前节点的父节点和当前节点的连接线
            var parentLink = this.tree.links(this.tree.nodes(self.draggingNode.parent));
            this.svgGroup.selectAll('path.link').filter(function (d, i) {  //从所有连接线中筛选出目标节点是当前拖拽节点id的连接线,然后删除掉
                if (d.target.id == self.draggingNode.id) {
                    return true;
                }
                return false;
            }).remove();

            self.dragStarted = null;  //开始拖拽标志位设置为假
        },

        // TODO: Pan function, can be better implemented.

        pan: function (domNode, direction) {
            var self = this;
            var speed = this.panSpeed;
            if (this.panTimer) {
                clearTimeout(this.panTimer);
                var translateCoords = d3.transform(this.svgGroup.attr("transform"));
                if (direction == 'left' || direction == 'right') {
                    var translateX = direction == 'left' ? translateCoords.translate[0] + speed : translateCoords.translate[0] - speed;
                    var translateY = translateCoords.translate[1];
                } else if (direction == 'up' || direction == 'down') {
                    var translateX = translateCoords.translate[0];
                    var translateY = direction == 'up' ? translateCoords.translate[1] + speed : translateCoords.translate[1] - speed;
                }
                var scaleX = translateCoords.scale[0];
                var scaleY = translateCoords.scale[1];
                var scale = this.zoomListener.scale();
                this.svgGroup.transition().attr("transform", "translate(" + translateX + "," + translateY + ")scale(" + scale + ")");
                d3.select(domNode).select('g.node').attr("transform", "translate(" + translateX + "," + translateY + ")");
                this.zoomListener.scale(this.zoomListener.scale());
                this.zoomListener.translate([translateX, translateY]);
                this.panTimer = setTimeout(function () {
                    self.pan(domNode, speed, direction);
                }, 50);
            }
        },

        //结束拖拽
        endDrag: function (domNode) {
            this.selectedNode = null;
            d3.selectAll('.ghostCircle').attr('class', 'ghostCircle');  //在结束拖拽后选择所有红色半透明大圆圈设置一个新的样式类,这个是隐藏功能
            d3.select(domNode).attr('class', 'node');  //
            // now restore the mouseover event or we won't be able to drag a 2nd time
            // 现在恢复鼠标移动的事件或对二次拖动不可用
            d3.select(domNode).select('.ghostCircle').attr('pointer-events', '');
            this.updateTempConnector();
            if (this.draggingNode !== null) {
                this.update(this.root);  //重新更新整个树
                this.centerNode(this.draggingNode);
                this.draggingNode = null;
            }
        },

        overCircle: function (d) {
            console.log('mouseover' + d.name)
            this.selectedNode = d;  //鼠标移动到某元素上,选择的节点变量等于当前鼠标移入的节点元素上,当拖拽到目标节点上时选择的节点变量就等于目标拖拽的节点
            this.updateTempConnector();  //更新临时连接者
        },

        outCircle: function (d) {
            console.log('mouseout' + d.name)
            this.selectedNode = null;  //鼠标从某元素上移开,当拖拽操作从
            this.updateTempConnector();  //更新临时连接者
        },

        // Function to update the temporary connector indicating dragging affiliation
        // 这个函数是表示拖拽关联中更新临时连接者
        updateTempConnector: function () {
            var data = [];
            if (this.draggingNode !== null && this.selectedNode !== null) {
                // have to flip the source coordinates since we did this for the existing connectors on the original tree
                data = [{
                    source: {
                        x: this.selectedNode.y0,
                        y: this.selectedNode.x0
                    },
                    target: {
                        x: this.draggingNode.y0,
                        y: this.draggingNode.x0
                    }
                }];
            }
            //  this.svgGroup = this.baseSvg.append("g");  //this.baseSvg = d3.select("#tree-container").append("svg")
            var link = this.svgGroup.selectAll(".templink").data(data);  //选择所有的临时连接线然后绑定连接线数据,这是从拖拽目标节点到当前拖拽节点的连接线

            link.enter().append("path")  //创建临时连接线
                .attr("class", "templink")
                .attr("d", d3.svg.diagonal())
                .attr('pointer-events', 'none');

            link.attr("d", d3.svg.diagonal());

            link.exit().remove();  //删除多余的临时连接线
        },

        // Function to center node when clicked/dropped so node doesn't get lost when collapsing/moving with large amount of children.

        centerNode: function (source) {
            var scale = this.zoomListener.scale();
            var x = -source.y0;
            var y = -source.x0;
            x = x * scale + this.viewerWidth / 2;
            y = y * scale + this.viewerHeight / 2 - 100;
            d3.select('g').transition()
                .duration(this.duration)
                .attr("transform", "translate(" + x + "," + y + ")scale(" + scale + ")");
            this.zoomListener.scale(scale);
            this.zoomListener.translate([x, y]);
        },

        firstShowNode: function (source) {
            var scale = this.zoomListener.scale();
            var x = -source.y0;
            var y = -source.x0;
            x = x * scale + 100;
            y = y * scale + this.viewerHeight / 2;
            d3.select('g').transition()
                .duration(this.duration)
                .attr("transform", "translate(" + x + "," + y + ")scale(" + scale + ")");
            this.zoomListener.scale(scale);
            this.zoomListener.translate([x, y]);
        },

        // Toggle children function  触发子节点函数

        toggleChildren: function (d) {
            if (d.children) {
                d._children = d.children;
                d.children = null;
            } else if (d._children) {
                d.children = d._children;
                d._children = null;
            }
            return d;
        },

        //更新节点
        update: function (source) {
            // Compute the new height, function counts total children of root node and sets tree height accordingly.
            // This prevents the layout looking squashed when new nodes are made visible or looking sparse when nodes are removed
            // This makes the layout more consistent.
            var i = 0;
            var self = this;

            var levelWidth = [1];  //定义层级的宽度 默认1层
            var childCount = function (level, n) {

                if (n.children && n.children.length > 0) {
                    if (levelWidth.length <= level + 1) levelWidth.push(0);

                    levelWidth[level + 1] += n.children.length;
                    n.children.forEach(function (d) {
                        childCount(level + 1, d);
                    });
                }
            };
            childCount(0, this.root);  //
            var newHeight = d3.max(levelWidth) * 25; // 25 pixels per line  设置新的高度,根据
            // 重新定义树状图布局的尺寸
            this.tree = this.tree.size([newHeight, this.viewerWidth]);  // var tree = d3.layout.tree().size([viewerHeight, viewerWidth]);

            // Compute the new tree layout.
            // 计算出新的树布局
            var nodes = this.tree.nodes(this.root).reverse(),
                links = this.tree.links(nodes);

            // Set widths between levels based on maxLabelLength.
            nodes.forEach(function (d) {
                //d.y = (d.depth * (self.maxLabelLength * 10)); //maxLabelLength * 10px
                d.y = (d.depth * 200); //maxLabelLength * 10px
                // alternatively to keep a fixed scale one can set a fixed depth per level
                // Normalize for fixed-depth by commenting out below line
                // d.y = (d.depth * 500); //500px per level.
            });

            // Update the nodes… 更新节点
            //  this.svgGroup = this.baseSvg.append("g");  //this.baseSvg = d3.select("#tree-container").append("svg")
            var node = this.svgGroup.selectAll("g.node")
                .data(nodes, function (d) {
                    return d.xyz_id || (d.xyz_id = ++i);
                    //return d.id = ++self.i;
                });

            // Enter any new nodes at the parent's previous position.
            //
            var nodeEnter = node.enter().append("g")
            //.call(self.dragListener)  //在节点组上调用拖拽监听
                .attr("class", "node")  //样式类是'node'
                .attr("transform", function (d) {
                    return "translate(" + source.y0 + "," + source.x0 + ")";
                })
                .on('click', function (d) {
                    self.click(d)
                }) //绑定单击的触发事件

            //在节点上增加圆
            nodeEnter.append("circle")
                .attr('class', 'nodeCircle')
                .attr("r", 0)
                .style("fill", function (d) {
                    return d._children ? "lightsteelblue" : "#fff";
                });

            //在节点上增加文本
            nodeEnter.append("text")
                .attr("x", function (d) {
                    return d.children || d._children ? -10 : 10;  //设置文字x坐标
                })
                .attr("dy", ".35em")
                .attr('class', 'nodeText')
                .attr("text-anchor", function (d) {
                    return d.children || d._children ? "end" : "start";  //文字的方向
                })
                .text(function (d) {
                    return d.name;  //设置文字内容
                })
                .style("fill-opacity", 0);  //设置透明度

            // phantom node to give us mouseover in a radius around it
            // 幻影节点给我们鼠标悬停在一个半径,用于节点拖拽时显示的红色半透明大圆圈
            nodeEnter.append("circle")
                .attr('class', 'ghostCircle')  //样式类别 隐藏 display: none;
                .attr("r", 30)  //半径
                .attr("opacity", 0.2)  // change this to zero to hide the target area 改变这个值设置为0隐藏目标区域,即设置为0就实现隐藏功能
                .style("fill", "red")
                .attr('pointer-events', 'mouseover')  //
                .on("mouseover", function (node) {  //鼠标移动到某元素上
                    self.overCircle(node);
                })
                .on("mouseout", function (node) {  //鼠标从某元素上移开
                    self.outCircle(node);
                });

            // Update the text to reflect whether node has children or not.
            // 更新节点的文本有子节点的节点和叶子节点


            node.select('text')
                .attr("x", function (d) {
                    return d.children || d._children ? -10 : 10;  //
                })
                .attr("text-anchor", function (d) {
                    return d.children || d._children ? "end" : "start";  //设置文字的方向
                })
                .text(function (d) {
                    return d.name;  //设置文本值
                })
                .on('click', function (d) {
                    self.click_text(d)
                }); //绑定单击的触发事件
            // Change the circle fill depending on whether it has children and is collapsed
            // 从所有节点选择
            node.select("circle.nodeCircle")
                .attr("r", 4.5)//半径是4.5
                .style("fill", function (d) {
                    return d._children ? "lightsteelblue" : "#fff";  //颜色填充,条件判断,有子节点高亮显示,如果没有子节点即位叶子节点填充的颜色就是白色
                });

            // Transition nodes to their new position.
            var nodeUpdate = node.transition()
                .duration(self.duration)
                .attr("transform", function (d) {
                    return "translate(" + d.y + "," + d.x + ")";
                });

            // Fade the text in  文本设置
            nodeUpdate.select("text")
                .style("fill-opacity", 1);

            // Transition exiting nodes to the parent's new position.
            var nodeExit = node.exit().transition()
                .duration(self.duration)
                .attr("transform", function (d) {
                    return "translate(" + source.y + "," + source.x + ")";
                })
                .remove();

            nodeExit.select("circle")
                .attr("r", 0);  //设置半径为0

            nodeExit.select("text")
                .style("fill-opacity", 0);  //设置透明度完全透明

            // Update the links…  更新链接线
            var link = this.svgGroup.selectAll("path.link")
                .data(links, function (d) {
                    return d.target.xyz_id;
                });

            // Enter any new links at the parent's previous position.
            link.enter().insert("path", "g")
                .attr("class", "link")
                .attr("d", function (d) {
                    var o = {
                        x: source.x0,
                        y: source.y0
                    };
                    return self.diagonal({
                        source: o,
                        target: o
                    });
                });

            // Transition links to their new position.
            link.transition()
                .duration(self.duration)
                .attr("d", self.diagonal);

            // Transition exiting nodes to the parent's new position.
            link.exit().transition()
                .duration(this.duration)
                .attr("d", function (d) {
                    var o = {
                        x: source.x,
                        y: source.y
                    };
                    return self.diagonal({
                        source: o,
                        target: o
                    });
                })
                .remove();

            // Stash the old positions for transition.
            nodes.forEach(function (d) {
                d.x0 = d.x;
                d.y0 = d.y;
            });
        },


        // Toggle children on click. 触发子节点的单击

        click: function (d) {
            var self = this;
            if (d3.event.defaultPrevented) return; // click suppressed
            /*
             if (this.open_action[d.model] != undefined){
             self.open_record(parseInt(d.id), d.model);
             return;
             };
             */
            d = this.toggleChildren(d);  //触发子节点函数
            this.update(d);  //更新节点
            this.centerNode(d);  //设置节点为中心位置
        },

        click_text: function (d) {
            var self = this;
            if (d3.event.defaultPrevented) return; // click suppressed
            d3.event.stopPropagation();
            if (this.open_action[d.model] != undefined) {
                self.open_record(parseInt(d.id), d.model);
                return;
            }
            ;
        },

        open_record: function (id, model) {

            var open_action = this.open_action[model]

            var self = this;
            new Model("ir.model.data").call("get_object_reference", [open_action[0], open_action[1]]).then(function (result) {
                var additional_context = _.extend({
                    active_id: id,
                    active_ids: [id],
                    active_model: model
                });
                return self.rpc("/web/action/load", {
                    action_id: result[1],
                    context: additional_context
                }).done(function (result) {
                    result.context = pyeval.eval('contexts', [result.context, additional_context]);
                    result.flags = result.flags || {};
                    result.flags.new_window = true;
                    result.res_id = id;
                    //result.target = "new";
                    return self.do_action(result, {
                        on_close: function () {
                            //self.do_search(self.last_domain, self.last_context, self.last_group_by);
                        }
                    });
                });
            });
        },

        get_test_date: function () {

            return {
                "name": "flare",
                "children": [
                    {
                        "name": "analytics",
                        "children": [
                            {
                                "name": "cluster",
                                "children": [
                                    {"name": "AgglomerativeCluster", "size": 3938},
                                    {"name": "CommunityStructure", "size": 3812},
                                    {"name": "HierarchicalCluster", "size": 6714},
                                    {"name": "MergeEdge", "size": 743}
                                ]
                            },
                            {
                                "name": "graph",
                                "children": [
                                    {"name": "BetweennessCentrality", "size": 3534},
                                    {"name": "LinkDistance", "size": 5731},
                                    {"name": "MaxFlowMinCut", "size": 7840},
                                    {"name": "ShortestPaths", "size": 5914},
                                    {"name": "SpanningTree", "size": 3416}
                                ]
                            },
                            {
                                "name": "optimization",
                                "children": [
                                    {"name": "AspectRatioBanker", "size": 7074}
                                ]
                            }
                        ]
                    }]

            };
        }


    });

    return Organization_Tree_Widget;
});
