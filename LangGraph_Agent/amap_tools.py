#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高德地图API工具集成
提供地理编码、搜索、路径规划、天气查询等完整功能
"""

import os
import json
import requests
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 高德地图API配置
AMAP_API_KEY = os.getenv('AMAP_API_KEY')
AMAP_BASE_URL = "https://restapi.amap.com"

# ============================================================================
# 地理编码相关工具
# ============================================================================

class GeocodeSchema(BaseModel):
    address: str = Field(description="结构化地址信息，如：北京市朝阳区阜通东大街6号")
    city: str = Field(default="", description="查询城市，可选：城市中文、citycode、adcode")

@tool(args_schema=GeocodeSchema)
def amap_geocode(address: str, city: str = "") -> str:
    """
    地理编码：将详细地址转换为经纬度坐标
    支持地标性建筑、门牌号等地址解析
    """
    try:
        url = f"{AMAP_BASE_URL}/v3/geocode/geo"
        params = {
            'key': AMAP_API_KEY,
            'address': address,
            'output': 'JSON'
        }
        if city:
            params['city'] = city
            
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == '1' and data['geocodes']:
            geocode = data['geocodes'][0]
            result = {
                'status': 'success',
                'address': address,
                'location': geocode['location'],
                'formatted_address': geocode.get('formatted_address', ''),
                'province': geocode.get('province', ''),
                'city': geocode.get('city', ''),
                'district': geocode.get('district', ''),
                'level': geocode.get('level', '')
            }
            return f"✅ 地理编码成功：\n地址：{address}\n坐标：{geocode['location']}\n详细信息：{json.dumps(result, ensure_ascii=False, indent=2)}"
        else:
            return f"❌ 地理编码失败：{data.get('info', '未知错误')}"
            
    except Exception as e:
        return f"❌ 地理编码请求失败：{str(e)}"

class RegeocodeSchema(BaseModel):
    location: str = Field(description="经纬度坐标，格式：经度,纬度，如：116.480881,39.989410")
    radius: int = Field(default=1000, description="搜索半径，单位：米，取值范围：0-3000")
    extensions: str = Field(default="base", description="返回结果控制：base(基本信息)或all(详细信息)")

@tool(args_schema=RegeocodeSchema)
def amap_regeocode(location: str, radius: int = 1000, extensions: str = "base") -> str:
    """
    逆地理编码：将经纬度坐标转换为详细地址
    返回地址描述及附近POI信息
    """
    try:
        url = f"{AMAP_BASE_URL}/v3/geocode/regeo"
        params = {
            'key': AMAP_API_KEY,
            'location': location,
            'radius': radius,
            'extensions': extensions,
            'output': 'JSON'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == '1':
            regeocode = data['regeocode']
            result = {
                'status': 'success',
                'location': location,
                'formatted_address': regeocode.get('formatted_address', ''),
                'address_component': regeocode.get('addressComponent', {}),
                'business_areas': regeocode.get('businessAreas', []),
            }
            
            # 如果是详细模式，添加POI信息
            if extensions == "all" and 'pois' in regeocode:
                result['nearby_pois'] = regeocode['pois'][:5]  # 只显示前5个POI
            
            return f"✅ 逆地理编码成功：\n坐标：{location}\n地址：{regeocode.get('formatted_address', '')}\n详细信息：{json.dumps(result, ensure_ascii=False, indent=2)}"
        else:
            return f"❌ 逆地理编码失败：{data.get('info', '未知错误')}"
            
    except Exception as e:
        return f"❌ 逆地理编码请求失败：{str(e)}"

# ============================================================================
# POI搜索相关工具  
# ============================================================================

class POISearchSchema(BaseModel):
    keywords: str = Field(description="搜索关键词，如：麦当劳、加油站、医院")
    city: str = Field(default="", description="搜索城市，如：北京、上海")
    types: str = Field(default="", description="POI类型，如：餐饮服务|生活服务")
    location: str = Field(default="", description="中心点坐标，如：116.480881,39.989410")
    radius: int = Field(default=3000, description="搜索半径，单位：米，最大50000")

@tool(args_schema=POISearchSchema)
def amap_poi_search(keywords: str, city: str = "", types: str = "", location: str = "", radius: int = 3000) -> str:
    """
    POI搜索：根据关键词搜索兴趣点
    支持关键词搜索、分类搜索、周边搜索等
    """
    try:
        url = f"{AMAP_BASE_URL}/v3/place/text"
        params = {
            'key': AMAP_API_KEY,
            'keywords': keywords,
            'output': 'JSON',
            'offset': 10,  # 每页记录数
            'page': 1
        }
        
        if city:
            params['city'] = city
        if types:
            params['types'] = types
        if location:
            params['location'] = location
            params['radius'] = radius
            
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == '1' and data['pois']:
            pois = data['pois'][:5]  # 只显示前5个结果
            results = []
            
            for poi in pois:
                poi_info = {
                    'name': poi.get('name', ''),
                    'type': poi.get('type', ''),
                    'address': poi.get('address', ''),
                    'location': poi.get('location', ''),
                    'tel': poi.get('tel', ''),
                    'distance': poi.get('distance', '')
                }
                results.append(poi_info)
            
            return f"✅ POI搜索成功，找到{data['count']}个结果：\n{json.dumps(results, ensure_ascii=False, indent=2)}"
        else:
            return f"❌ POI搜索失败：{data.get('info', '未找到相关结果')}"
            
    except Exception as e:
        return f"❌ POI搜索请求失败：{str(e)}"

class InputTipsSchema(BaseModel):
    keywords: str = Field(description="输入的关键词")
    city: str = Field(default="", description="搜索城市")
    datatype: str = Field(default="all", description="数据类型：all|poi|bus|busline")

@tool(args_schema=InputTipsSchema)
def amap_input_tips(keywords: str, city: str = "", datatype: str = "all") -> str:
    """
    输入提示：根据用户输入返回搜索建议
    适用于搜索框自动补全功能
    """
    try:
        url = f"{AMAP_BASE_URL}/v3/assistant/inputtips"
        params = {
            'key': AMAP_API_KEY,
            'keywords': keywords,
            'datatype': datatype,
            'output': 'JSON'
        }
        
        if city:
            params['city'] = city
            
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == '1' and data['tips']:
            tips = data['tips'][:8]  # 显示前8个建议
            suggestions = []
            
            for tip in tips:
                suggestion = {
                    'name': tip.get('name', ''),
                    'district': tip.get('district', ''),
                    'address': tip.get('address', ''),
                    'location': tip.get('location', '')
                }
                suggestions.append(suggestion)
            
            return f"✅ 搜索建议：\n{json.dumps(suggestions, ensure_ascii=False, indent=2)}"
        else:
            return f"❌ 搜索建议失败：{data.get('info', '未找到建议')}"
            
    except Exception as e:
        return f"❌ 搜索建议请求失败：{str(e)}"

# ============================================================================
# 路径规划相关工具
# ============================================================================

class RouteSchema(BaseModel):
    origin: str = Field(description="起点坐标，格式：经度,纬度")
    destination: str = Field(description="终点坐标，格式：经度,纬度")
    strategy: int = Field(default=0, description="路径策略：0-速度优先，1-费用优先，2-距离优先，3-不走高速")
    waypoints: str = Field(default="", description="途经点，多个坐标用|分隔")

@tool(args_schema=RouteSchema)
def amap_driving_route(origin: str, destination: str, strategy: int = 0, waypoints: str = "") -> str:
    """
    驾车路径规划：规划两点间驾车路线
    支持多种策略和途经点设置
    """
    try:
        url = f"{AMAP_BASE_URL}/v3/direction/driving"
        params = {
            'key': AMAP_API_KEY,
            'origin': origin,
            'destination': destination,
            'strategy': strategy,
            'output': 'JSON',
            'extensions': 'base'
        }
        
        if waypoints:
            params['waypoints'] = waypoints
            
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == '1' and data['route']['paths']:
            path = data['route']['paths'][0]
            result = {
                'status': 'success',
                'origin': origin,
                'destination': destination,
                'distance': f"{int(path['distance'])/1000:.2f}公里",
                'duration': f"{int(path['duration'])//60}分钟",
                'toll_distance': f"{int(path.get('tolls', 0))/1000:.2f}公里",
                'toll_fee': f"{path.get('toll_distance', 0)}元",
                'traffic_lights': path.get('traffic_lights', 0),
                'strategy_name': ['速度优先', '费用优先', '距离优先', '不走高速'][strategy]
            }
            
            return f"✅ 驾车路径规划成功：\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        else:
            return f"❌ 驾车路径规划失败：{data.get('info', '未知错误')}"
            
    except Exception as e:
        return f"❌ 驾车路径规划请求失败：{str(e)}"

class WalkingRouteSchema(BaseModel):
    origin: str = Field(description="起点坐标，格式：经度,纬度")
    destination: str = Field(description="终点坐标，格式：经度,纬度")

@tool(args_schema=WalkingRouteSchema)
def amap_walking_route(origin: str, destination: str) -> str:
    """
    步行路径规划：规划两点间步行路线
    """
    try:
        url = f"{AMAP_BASE_URL}/v3/direction/walking"
        params = {
            'key': AMAP_API_KEY,
            'origin': origin,
            'destination': destination,
            'output': 'JSON'
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == '1' and data['route']['paths']:
            path = data['route']['paths'][0]
            result = {
                'status': 'success',
                'origin': origin,
                'destination': destination,
                'distance': f"{int(path['distance'])/1000:.2f}公里",
                'duration': f"{int(path['duration'])//60}分钟"
            }
            
            return f"✅ 步行路径规划成功：\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        else:
            return f"❌ 步行路径规划失败：{data.get('info', '未知错误')}"
            
    except Exception as e:
        return f"❌ 步行路径规划请求失败：{str(e)}"

# ============================================================================
# 天气查询工具
# ============================================================================

class WeatherSchema(BaseModel):
    city: str = Field(description="城市adcode编码或城市名称，如：110101(北京)、上海")
    extensions: str = Field(default="base", description="气象类型：base(实况天气)或all(预报天气)")

@tool(args_schema=WeatherSchema)
def amap_weather(city: str, extensions: str = "base") -> str:
    """
    天气查询：查询指定城市的实时天气或天气预报
    """
    try:
        url = f"{AMAP_BASE_URL}/v3/weather/weatherInfo"
        params = {
            'key': AMAP_API_KEY,
            'city': city,
            'extensions': extensions,
            'output': 'JSON'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == '1':
            if extensions == "base" and 'lives' in data:
                # 实况天气
                live = data['lives'][0]
                result = {
                    'type': '实况天气',
                    'city': live['city'],
                    'weather': live['weather'],
                    'temperature': f"{live['temperature']}°C",
                    'wind_direction': live['winddirection'],
                    'wind_power': f"{live['windpower']}级",
                    'humidity': f"{live['humidity']}%",
                    'report_time': live['reporttime']
                }
            elif extensions == "all" and 'forecasts' in data:
                # 预报天气
                forecast = data['forecasts'][0]
                result = {
                    'type': '天气预报',
                    'city': forecast['city'],
                    'report_time': forecast['reporttime'],
                    'forecasts': []
                }
                
                for cast in forecast['casts'][:3]:  # 显示3天预报
                    day_forecast = {
                        'date': cast['date'],
                        'week': cast['week'],
                        'day_weather': cast['dayweather'],
                        'night_weather': cast['nightweather'],
                        'day_temp': f"{cast['daytemp']}°C",
                        'night_temp': f"{cast['nighttemp']}°C",
                        'day_wind': f"{cast['daywind']} {cast['daypower']}级",
                        'night_wind': f"{cast['nightwind']} {cast['nightpower']}级"
                    }
                    result['forecasts'].append(day_forecast)
            
            return f"✅ 天气查询成功：\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        else:
            return f"❌ 天气查询失败：{data.get('info', '未知错误')}"
            
    except Exception as e:
        return f"❌ 天气查询请求失败：{str(e)}"

# ============================================================================
# 坐标转换工具
# ============================================================================

class CoordConvertSchema(BaseModel):
    locations: str = Field(description="坐标点，多个坐标用|分隔，格式：经度,纬度")
    coordsys: str = Field(default="gps", description="原坐标系：gps|mapbar|baidu|autonavi")

@tool(args_schema=CoordConvertSchema)
def amap_coord_convert(locations: str, coordsys: str = "gps") -> str:
    """
    坐标转换：将其他坐标系转换为高德坐标系
    支持GPS、百度、图吧等坐标系
    """
    try:
        url = f"{AMAP_BASE_URL}/v3/assistant/coordinate/convert"
        params = {
            'key': AMAP_API_KEY,
            'locations': locations,
            'coordsys': coordsys,
            'output': 'JSON'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == '1':
            result = {
                'status': 'success',
                'original_coords': locations,
                'original_system': coordsys,
                'converted_coords': data['locations'],
                'target_system': '高德坐标系(GCJ02)'
            }
            
            return f"✅ 坐标转换成功：\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        else:
            return f"❌ 坐标转换失败：{data.get('info', '未知错误')}"
            
    except Exception as e:
        return f"❌ 坐标转换请求失败：{str(e)}"

# ============================================================================
# IP定位工具
# ============================================================================

class IPLocationSchema(BaseModel):
    ip: str = Field(default="", description="IP地址，为空则使用请求来源IP")

@tool(args_schema=IPLocationSchema)
def amap_ip_location(ip: str = "") -> str:
    """
    IP定位：根据IP地址获取大致位置信息
    """
    try:
        url = f"{AMAP_BASE_URL}/v3/ip"
        params = {
            'key': AMAP_API_KEY,
            'output': 'JSON'
        }
        
        if ip:
            params['ip'] = ip
            
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == '1':
            result = {
                'status': 'success',
                'ip': ip or '来源IP',
                'province': data.get('province', ''),
                'city': data.get('city', ''),
                'adcode': data.get('adcode', ''),
                'rectangle': data.get('rectangle', '')
            }
            
            return f"✅ IP定位成功：\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        else:
            return f"❌ IP定位失败：{data.get('info', '未知错误')}"
            
    except Exception as e:
        return f"❌ IP定位请求失败：{str(e)}"

# ============================================================================
# 行政区域查询工具
# ============================================================================

class DistrictSchema(BaseModel):
    keywords: str = Field(default="", description="行政区名称，如：北京、朝阳区")
    subdistrict: int = Field(default=1, description="显示下级行政区级数：0-3")
    extensions: str = Field(default="base", description="返回信息：base(基本)或all(包含边界)")

@tool(args_schema=DistrictSchema)
def amap_district_search(keywords: str = "", subdistrict: int = 1, extensions: str = "base") -> str:
    """
    行政区域查询：查询省市区行政区域信息
    可获取行政区边界、下级行政区等信息
    """
    try:
        url = f"{AMAP_BASE_URL}/v3/config/district"
        params = {
            'key': AMAP_API_KEY,
            'keywords': keywords,
            'subdistrict': subdistrict,
            'extensions': extensions,
            'output': 'JSON'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == '1' and data['districts']:
            districts = data['districts']
            results = []
            
            for district in districts[:5]:  # 显示前5个结果
                district_info = {
                    'name': district.get('name', ''),
                    'center': district.get('center', ''),
                    'adcode': district.get('adcode', ''),
                    'level': district.get('level', ''),
                    'districts': [sub.get('name', '') for sub in district.get('districts', [])[:10]]
                }
                results.append(district_info)
            
            return f"✅ 行政区域查询成功：\n{json.dumps(results, ensure_ascii=False, indent=2)}"
        else:
            return f"❌ 行政区域查询失败：{data.get('info', '未找到相关区域')}"
            
    except Exception as e:
        return f"❌ 行政区域查询请求失败：{str(e)}"

# 导出所有工具
AMAP_TOOLS = [
    amap_geocode,
    amap_regeocode,
    amap_poi_search,
    amap_input_tips,
    amap_driving_route,
    amap_walking_route,
    amap_weather,
    amap_coord_convert,
    amap_ip_location,
    amap_district_search
] 