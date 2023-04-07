resource "datadog_dashboard_json" "sandbox_overview" {
  dashboard = <<END
{
	"title": "Sanbox Overview",
	"description": "",
	"widgets": [{
		"id": 8191766806311579,
		"definition": {
			"title": "# Requests",
			"title_size": "16",
			"title_align": "left",
			"show_legend": false,
			"legend_layout": "auto",
			"legend_columns": ["avg", "min", "max", "value", "sum"],
			"type": "timeseries",
			"requests": [{
				"formulas": [{
					"style": {
						"palette": "warm",
						"palette_index": 4
					},
					"alias": "errors",
					"formula": "query2"
				}, {
					"style": {
						"palette": "green",
						"palette_index": 3
					},
					"alias": "success",
					"formula": "query1 - query2"
				}],
				"queries": [{
					"name": "query2",
					"data_source": "metrics",
					"query": "sum:trace.flask.request.errors{env:test,service:flask,resource_name:post_/count/_user_id}.as_count()"
				}, {
					"name": "query1",
					"data_source": "metrics",
					"query": "sum:trace.flask.request.hits{env:test,service:flask,resource_name:post_/count/_user_id}.as_count()"
				}],
				"response_format": "timeseries",
				"style": {
					"palette": "dog_classic",
					"line_type": "solid",
					"line_width": "normal"
				},
				"display_type": "bars"
			}]
		},
		"layout": {
			"x": 0,
			"y": 0,
			"width": 5,
			"height": 2
		}
	}, {
		"id": 6775354012142785,
		"definition": {
			"title": "Latency",
			"title_size": "16",
			"title_align": "left",
			"show_legend": false,
			"legend_layout": "auto",
			"legend_columns": ["avg", "min", "max", "value", "sum"],
			"type": "timeseries",
			"requests": [{
				"formulas": [{
					"formula": "p90"
				}],
				"queries": [{
					"data_source": "metrics",
					"name": "p90",
					"query": "p90:trace.flask.request{env:test,service:flask,resource_name:post_/count/_user_id}"
				}],
				"response_format": "timeseries",
				"style": {
					"palette": "dog_classic",
					"line_type": "solid",
					"line_width": "normal"
				},
				"display_type": "line"
			}, {
				"formulas": [{
					"formula": "max"
				}],
				"queries": [{
					"data_source": "metrics",
					"name": "max",
					"query": "max:trace.flask.request{env:test,resource_name:post_/count/_user_id,service:flask}"
				}],
				"response_format": "timeseries",
				"style": {
					"palette": "dog_classic",
					"line_type": "solid",
					"line_width": "normal"
				},
				"display_type": "line"
			}]
		},
		"layout": {
			"x": 5,
			"y": 0,
			"width": 5,
			"height": 2
		}
	}],
	"template_variables": [],
	"layout_type": "ordered",
	"notify_list": [],
	"reflow_type": "fixed",
	"id": "r9b-pk6-hip"
}

END
}