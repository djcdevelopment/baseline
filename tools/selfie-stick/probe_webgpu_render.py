#!/usr/bin/env python3
"""R&D probe: does WebGPU instancing clear the CSS DOM ceiling?

The CSS lap proved exact world-save geometry can become a recognizable building and
found its first edge at 847 pieces / 5,082 DOM faces.  This lap preserves the same
data receipt and visual controls while replacing those faces with one unit cube and
an 80-byte GPU instance record per piece.

The pilot is cluster 1820's 847-piece connected structure.  If hardware WebGPU and
visual/mechanical parity hold, the only scale sample is every known-geometry member
of frozen cluster 182.  One edge ends the lap; there is no WebGL fallback or LOD.

Usage:
  python probe_webgpu_render.py
  python probe_webgpu_render.py --pilot-only
  python probe_webgpu_render.py --no-browser
"""

import argparse
import base64
import functools
import json
import math
import os
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.request
from collections import Counter
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

import duckdb
import numpy as np

from probe_css_render import (
    ARCH,
    DEFAULT_BUILDING_GEOMETRY,
    DEFAULT_CLUSTER_POINTS,
    find_browser,
    load_cluster,
    load_rotation_receipt,
    oriented_bounds,
)
from reconstruct_cluster import FAMILY_COLORS, load_geometry
from segment_buildings import segment
from sight import looks_like_vegetation


HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "out" / "era17" / "webgpu-render"
INSTANCE_FLOATS = 20
INSTANCE_BYTES = INSTANCE_FLOATS * 4


HTML = r'''<!doctype html>
<html lang="en" data-ready="false">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>World bytes → WebGPU</title>
<style>
  :root { color-scheme:dark; --slate:#101418; --panel:#181e23; --ink:#e7edf1;
    --muted:#92a0aa; --ochre:#d79a3b; --line:#34414a; }
  * { box-sizing:border-box; }
  html,body { width:100%; height:100%; margin:0; overflow:hidden; background:var(--slate);
    color:var(--ink); font:14px/1.35 system-ui,-apple-system,"Segoe UI",sans-serif; }
  body { display:grid; grid-template-columns:292px minmax(0,1fr); }
  aside { position:relative; z-index:2; padding:22px 20px; overflow:auto;
    background:linear-gradient(155deg,#1d2429,#12171b 72%); border-right:1px solid var(--line); }
  .eyebrow { color:var(--ochre); font:700 11px/1.2 ui-monospace,monospace;
    letter-spacing:.14em; text-transform:uppercase; }
  h1 { margin:8px 0 5px; font-size:23px; font-weight:590; letter-spacing:-.03em; }
  .sub { color:var(--muted); margin-bottom:18px; }
  .metric { display:grid; grid-template-columns:1fr auto; gap:4px 12px; padding:8px 0;
    border-top:1px solid var(--line); }
  .metric span { color:var(--muted); } .metric output { font-family:ui-monospace,monospace; }
  .section { margin-top:17px; }
  .label { display:block; margin-bottom:7px; color:var(--muted); font-size:11px;
    font-weight:700; letter-spacing:.1em; text-transform:uppercase; }
  .row { display:flex; flex-wrap:wrap; gap:6px; }
  button { appearance:none; border:1px solid #47545c; border-radius:3px; padding:6px 9px;
    background:#20282e; color:var(--ink); cursor:pointer; }
  button:hover,button[aria-pressed="true"] { border-color:var(--ochre); color:#ffd58d; }
  #families { display:grid; grid-template-columns:1fr 1fr; gap:5px 10px; }
  #families label { display:flex; min-width:0; align-items:center; gap:6px; color:#c6d0d6; }
  #families i { width:9px; height:9px; flex:0 0 auto; background:var(--swatch); }
  #families small { color:var(--muted); margin-left:auto; }
  #status { margin-top:16px; color:#aebac1; font:11px/1.45 ui-monospace,monospace;
    white-space:pre-wrap; }
  #live-controls[hidden] { display:none; }
  .placement { display:grid; grid-template-columns:1fr 1fr; gap:7px; }
  .placement label { color:var(--muted); font:11px ui-monospace,monospace; }
  .placement input { width:100%; margin-top:3px; border:1px solid #47545c; border-radius:3px;
    padding:6px 7px; background:#10161a; color:var(--ink); font:12px ui-monospace,monospace; }
  button.primary { border-color:var(--ochre); background:#5b3c15; color:#ffe0a7; }
  button:disabled { opacity:.45; cursor:wait; }
  #live-result { max-height:150px; overflow:auto; color:#aebac1; font:11px/1.4 ui-monospace,monospace;
    white-space:pre-wrap; }
  main { position:relative; min-width:0; overflow:hidden; cursor:grab; background:
    radial-gradient(circle at 50% 46%,rgba(91,116,128,.13),transparent 44%),
    linear-gradient(rgba(255,255,255,.022) 1px,transparent 1px),
    linear-gradient(90deg,rgba(255,255,255,.022) 1px,transparent 1px);
    background-size:auto,40px 40px,40px 40px; }
  main:active { cursor:grabbing; }
  canvas { display:block; width:100%; height:100%; }
  .hint { position:absolute; right:15px; bottom:12px; color:#71808a; font:11px ui-monospace,monospace; }
  #receipt { display:none; }
</style>
</head>
<body>
<aside>
  <div class="eyebrow">Buildings from bytes / WebGPU probe</div>
  <h1 id="title">Loading scene</h1><div class="sub" id="subtitle"></div>
  <div class="metric"><span>instances</span><output id="pieces">—</output></div>
  <div class="metric"><span>triangles</span><output id="triangles">—</output></div>
  <div class="metric"><span>instance buffer</span><output id="bytes">—</output></div>
  <div class="metric"><span>adapter</span><output id="adapter">—</output></div>
  <div class="section"><span class="label">Surface</span><div class="row">
    <button type="button" data-mode="solid" aria-pressed="true">GPU solid</button>
    <button type="button" data-mode="wire" aria-pressed="false">GPU wireframe</button>
  </div></div>
  <div class="section"><span class="label">Known views</span><div class="row">
    <button type="button" data-view="iso">Isometric</button>
    <button type="button" data-view="end-a">78.8° end</button>
    <button type="button" data-view="end-b">258.8° end</button>
  </div></div>
  <div class="section"><span class="label">Families</span><div id="families"></div></div>
  <section id="live-controls" class="section" hidden>
    <span class="label">Live Valheim placement</span>
    <div class="placement">
      <label>X<input id="world-x" type="number" step="0.1"></label>
      <label>Y / height<input id="world-y" type="number" step="0.1"></label>
      <label>Z<input id="world-z" type="number" step="0.1"></label>
      <label>Yaw degrees<input id="world-yaw" type="number" step="1"></label>
    </div>
    <div class="row" style="margin-top:9px">
      <button id="apply-live" type="button" class="primary">Apply in Valheim</button>
      <button id="clear-live" type="button">Clear marked build</button>
    </div>
    <pre id="live-result">same process · fixed mailbox · waiting</pre>
  </section>
  <div id="status">requesting hardware adapter…</div>
</aside>
<main id="stage"><canvas id="gpu"></canvas><div class="hint">drag to orbit · wheel to zoom</div></main>
<pre id="receipt">pending</pre>
<script type="module">
const PAGE_STARTED = performance.now();
const params = new URLSearchParams(location.search);
const receiptNode = document.getElementById('receipt');
const statusNode = document.getElementById('status');
const errors = [];
let deviceLost = false;

function publish(value) {
  window.__webgpuReceipt = value;
  receiptNode.textContent = JSON.stringify(value);
}
function fail(error) {
  const message = error?.stack || error?.message || String(error);
  statusNode.textContent = `BLOCKED\n${message}`;
  publish({schema:'webgpu-zdo-browser/v1',status:'error',error:message,
    validation_errors:errors,device_lost:deviceLost});
  document.documentElement.dataset.ready='error';
}
const percentile = (values,p) => {
  const sorted=[...values].sort((a,b)=>a-b);
  return sorted[Math.max(0,Math.ceil(sorted.length*p)-1)];
};
const frame = () => new Promise(resolve => requestAnimationFrame(resolve));

function multiply(a,b) {
  const out=new Float32Array(16);
  for(let c=0;c<4;c++) for(let r=0;r<4;r++) {
    let sum=0; for(let k=0;k<4;k++) sum+=a[k*4+r]*b[c*4+k];
    out[c*4+r]=sum;
  }
  return out;
}
function perspective(fovy,aspect,near,far) {
  const f=1/Math.tan(fovy/2),out=new Float32Array(16);
  out[0]=f/aspect; out[5]=f; out[10]=(far+near)/(near-far); out[11]=-1;
  out[14]=(2*far*near)/(near-far); return out;
}
const sub=(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]];
const dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const norm=a=>{const n=Math.hypot(...a)||1;return a.map(v=>v/n)};
function lookAt(eye,target,up) {
  const z=norm(sub(eye,target)),x=norm(cross(up,z)),y=cross(z,x);
  return new Float32Array([x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,
    -dot(x,eye),-dot(y,eye),-dot(z,eye),1]);
}
function adapterRecord(info) {
  const keys=['vendor','architecture','device','description','type','backend','d3dShaderModel'];
  const out={}; for(const key of keys) { try { if(info?.[key]!==undefined) out[key]=info[key]; } catch(_){} }
  return out;
}
function classifyAdapter(info) {
  const text=Object.values(info).join(' ').toLowerCase();
  if(/swiftshader|software|llvmpipe|warp|fallback|cpu/.test(text)) return 'software';
  if(/discrete gpu|integrated gpu|intel|nvidia|amd|radeon|arc|geforce/.test(text)) return 'hardware';
  return 'unknown';
}
function gpuBuffer(device,data,usage,label) {
  const buffer=device.createBuffer({label,size:(data.byteLength+3)&~3,usage,mappedAtCreation:true});
  new data.constructor(buffer.getMappedRange()).set(data); buffer.unmap(); return buffer;
}

async function main() {
  if(!navigator.gpu) throw new Error('navigator.gpu is unavailable');
  const [manifest,instanceData] = await Promise.all([
    fetch('scene.json').then(r=>{if(!r.ok)throw new Error(`scene.json ${r.status}`);return r.json()}),
    fetch('scene.bin').then(r=>{if(!r.ok)throw new Error(`scene.bin ${r.status}`);return r.arrayBuffer()})
  ]);
  if(instanceData.byteLength!==manifest.instance_bytes)
    throw new Error(`instance bytes ${instanceData.byteLength} != ${manifest.instance_bytes}`);
  const adapter=await navigator.gpu.requestAdapter({powerPreference:'high-performance'});
  if(!adapter) throw new Error('requestAdapter returned null');
  const adapterInfo=adapterRecord(adapter.info);
  const adapterClass=classifyAdapter(adapterInfo);
  const device=await adapter.requestDevice();
  device.addEventListener('uncapturederror',event=>{errors.push(String(event.error?.message||event.error));});
  device.lost.then(info=>{deviceLost=true;errors.push(`device lost: ${info.reason} ${info.message}`);});

  const canvas=document.getElementById('gpu'),stage=document.getElementById('stage');
  const context=canvas.getContext('webgpu');
  if(!context) throw new Error('webgpu canvas context unavailable');
  const format=navigator.gpu.getPreferredCanvasFormat();
  let depthTexture;
  function resize() {
    const scale=Math.min(devicePixelRatio||1,2);
    const w=Math.max(1,Math.floor(stage.clientWidth*scale));
    const h=Math.max(1,Math.floor(stage.clientHeight*scale));
    if(canvas.width===w&&canvas.height===h) return;
    canvas.width=w; canvas.height=h;
    context.configure({device,format,alphaMode:'opaque'});
    if(depthTexture) depthTexture.destroy();
    depthTexture=device.createTexture({size:[w,h],format:'depth24plus',
      usage:GPUTextureUsage.RENDER_ATTACHMENT});
  }

  const solidVertices=new Float32Array([
    -.5,-.5, .5,0,0,1, .5,-.5, .5,0,0,1, .5,.5, .5,0,0,1, -.5,.5, .5,0,0,1,
     .5,-.5,-.5,0,0,-1,-.5,-.5,-.5,0,0,-1,-.5,.5,-.5,0,0,-1, .5,.5,-.5,0,0,-1,
     .5,-.5, .5,1,0,0, .5,-.5,-.5,1,0,0, .5,.5,-.5,1,0,0, .5,.5, .5,1,0,0,
    -.5,-.5,-.5,-1,0,0,-.5,-.5, .5,-1,0,0,-.5,.5, .5,-1,0,0,-.5,.5,-.5,-1,0,0,
    -.5,.5, .5,0,1,0, .5,.5, .5,0,1,0, .5,.5,-.5,0,1,0,-.5,.5,-.5,0,1,0,
    -.5,-.5,-.5,0,-1,0, .5,-.5,-.5,0,-1,0, .5,-.5, .5,0,-1,0,-.5,-.5, .5,0,-1,0
  ]);
  const solidIndices=new Uint16Array([
    0,1,2,0,2,3,4,5,6,4,6,7,8,9,10,8,10,11,12,13,14,12,14,15,
    16,17,18,16,18,19,20,21,22,20,22,23]);
  const lineVertices=new Float32Array([
    -.5,-.5,-.5,-.5,-.5,.5,-.5,.5,-.5,-.5,.5,.5,
     .5,-.5,-.5, .5,-.5,.5, .5,.5,-.5, .5,.5,.5]);
  const lineIndices=new Uint16Array([0,1,0,2,0,4,1,3,1,5,2,3,2,6,3,7,4,5,4,6,5,7,6,7]);
  const solidVB=gpuBuffer(device,solidVertices,GPUBufferUsage.VERTEX,'solid cube');
  const solidIB=gpuBuffer(device,solidIndices,GPUBufferUsage.INDEX,'solid indices');
  const lineVB=gpuBuffer(device,lineVertices,GPUBufferUsage.VERTEX,'edge cube');
  const lineIB=gpuBuffer(device,lineIndices,GPUBufferUsage.INDEX,'edge indices');
  const instanceBuffer=gpuBuffer(device,new Float32Array(instanceData),GPUBufferUsage.VERTEX,'ZDO instances');
  const cameraBuffer=device.createBuffer({size:64,usage:GPUBufferUsage.UNIFORM|GPUBufferUsage.COPY_DST});

  const shader=device.createShaderModule({code:`
    struct Camera { viewProjection:mat4x4<f32> }
    @group(0) @binding(0) var<uniform> camera:Camera;
    struct SolidIn {
      @location(0) position:vec3f, @location(1) normal:vec3f,
      @location(2) m0:vec4f, @location(3) m1:vec4f,
      @location(4) m2:vec4f, @location(5) m3:vec4f, @location(6) color:vec4f
    }
    struct SolidOut { @builtin(position) position:vec4f,
      @location(0) color:vec4f, @location(1) normal:vec3f }
    @vertex fn solidVS(input:SolidIn)->SolidOut {
      let model=mat4x4f(input.m0,input.m1,input.m2,input.m3);
      let basis=mat3x3f(normalize(input.m0.xyz),normalize(input.m1.xyz),normalize(input.m2.xyz));
      var out:SolidOut; out.position=camera.viewProjection*model*vec4f(input.position,1);
      out.color=input.color; out.normal=basis*input.normal; return out;
    }
    @fragment fn solidFS(input:SolidOut)->@location(0) vec4f {
      let light=0.28+0.72*max(dot(normalize(input.normal),normalize(vec3f(-.45,.8,.32))),0);
      return vec4f(input.color.rgb*light,1);
    }
    struct LineIn { @location(0) position:vec3f,
      @location(2) m0:vec4f, @location(3) m1:vec4f,
      @location(4) m2:vec4f, @location(5) m3:vec4f, @location(6) color:vec4f }
    struct LineOut { @builtin(position) position:vec4f, @location(0) color:vec4f }
    @vertex fn lineVS(input:LineIn)->LineOut {
      let model=mat4x4f(input.m0,input.m1,input.m2,input.m3);
      var out:LineOut; out.position=camera.viewProjection*model*vec4f(input.position,1);
      out.color=vec4f(min(input.color.rgb*1.25,vec3f(1)),1); return out;
    }
    @fragment fn lineFS(input:LineOut)->@location(0) vec4f { return input.color; }
  `});
  const instanceLayout={arrayStride:80,stepMode:'instance',attributes:[
    {shaderLocation:2,offset:0,format:'float32x4'},{shaderLocation:3,offset:16,format:'float32x4'},
    {shaderLocation:4,offset:32,format:'float32x4'},{shaderLocation:5,offset:48,format:'float32x4'},
    {shaderLocation:6,offset:64,format:'float32x4'}]};
  const bindLayout=device.createBindGroupLayout({entries:[{binding:0,visibility:GPUShaderStage.VERTEX,
    buffer:{type:'uniform'}}]});
  const pipelineLayout=device.createPipelineLayout({bindGroupLayouts:[bindLayout]});
  const depthStencil={format:'depth24plus',depthWriteEnabled:true,depthCompare:'less'};
  const solidPipeline=device.createRenderPipeline({layout:pipelineLayout,
    vertex:{module:shader,entryPoint:'solidVS',buffers:[{arrayStride:24,attributes:[
      {shaderLocation:0,offset:0,format:'float32x3'},{shaderLocation:1,offset:12,format:'float32x3'}]},instanceLayout]},
    fragment:{module:shader,entryPoint:'solidFS',targets:[{format}]},
    primitive:{topology:'triangle-list',cullMode:'back'},depthStencil});
  const linePipeline=device.createRenderPipeline({layout:pipelineLayout,
    vertex:{module:shader,entryPoint:'lineVS',buffers:[{arrayStride:12,attributes:[
      {shaderLocation:0,offset:0,format:'float32x3'}]},instanceLayout]},
    fragment:{module:shader,entryPoint:'lineFS',targets:[{format}]},
    primitive:{topology:'line-list'},depthStencil});
  const bindGroup=device.createBindGroup({layout:bindLayout,entries:[{binding:0,
    resource:{buffer:cameraBuffer}}]});

  let yaw=-35,pitch=-28,zoom=1,mode=params.get('mode')==='wire'?'wire':'solid';
  const visible=new Set(manifest.families.map((_,i)=>i));
  function cameraMatrix() {
    const yr=yaw*Math.PI/180,pr=pitch*Math.PI/180;
    const distance=manifest.radius_m*2.45/zoom;
    const eye=[Math.sin(yr)*Math.cos(pr)*distance,Math.sin(pr)*distance,
      Math.cos(yr)*Math.cos(pr)*distance];
    return multiply(perspective(42*Math.PI/180,canvas.width/canvas.height,
      Math.max(.05,manifest.radius_m*.002),manifest.radius_m*8),lookAt(eye,[0,0,0],[0,1,0]));
  }
  function render() {
    resize(); device.queue.writeBuffer(cameraBuffer,0,cameraMatrix());
    const encoder=device.createCommandEncoder();
    const pass=encoder.beginRenderPass({colorAttachments:[{view:context.getCurrentTexture().createView(),
      clearValue:{r:.04,g:.055,b:.065,a:1},loadOp:'clear',storeOp:'store'}],
      depthStencilAttachment:{view:depthTexture.createView(),depthClearValue:1,
        depthLoadOp:'clear',depthStoreOp:'store'}});
    const wire=mode==='wire';
    pass.setPipeline(wire?linePipeline:solidPipeline); pass.setBindGroup(0,bindGroup);
    pass.setVertexBuffer(0,wire?lineVB:solidVB); pass.setVertexBuffer(1,instanceBuffer);
    pass.setIndexBuffer(wire?lineIB:solidIB,'uint16');
    for(let i=0;i<manifest.families.length;i++) if(visible.has(i)) {
      const range=manifest.families[i]; pass.drawIndexed(wire?24:36,range.count,0,0,range.start);
    }
    pass.end(); device.queue.submit([encoder.finish()]);
  }
  function setView(name) {
    const views={iso:[28,-35],'end-a':[10,78.8],'end-b':[10,258.8]};
    [pitch,yaw]=views[name]||views.iso; zoom=1; render();
  }
  function setMode(value) {
    mode=value==='wire'?'wire':'solid';
    for(const button of document.querySelectorAll('[data-mode]'))
      button.setAttribute('aria-pressed',button.dataset.mode===mode);
    render();
  }
  for(const button of document.querySelectorAll('[data-view]'))
    button.addEventListener('click',()=>setView(button.dataset.view));
  for(const button of document.querySelectorAll('[data-mode]'))
    button.addEventListener('click',()=>setMode(button.dataset.mode));
  const familyBox=document.getElementById('families');
  manifest.families.forEach((family,index)=>{
    const label=document.createElement('label'),input=document.createElement('input');
    input.type='checkbox';input.checked=true;input.addEventListener('change',()=>{
      input.checked?visible.add(index):visible.delete(index);render();});
    const swatch=document.createElement('i');swatch.style.setProperty('--swatch',family.color);
    const name=document.createElement('span');name.textContent=family.name;
    const count=document.createElement('small');count.textContent=family.count;
    label.append(input,swatch,name,count);familyBox.appendChild(label);
  });
  let dragging=false,lastX=0,lastY=0;
  stage.addEventListener('pointerdown',event=>{dragging=true;lastX=event.clientX;lastY=event.clientY;
    stage.setPointerCapture(event.pointerId)});
  stage.addEventListener('pointermove',event=>{if(!dragging)return;
    yaw+=(event.clientX-lastX)*.35;pitch+=(event.clientY-lastY)*.25;
    pitch=Math.max(-88,Math.min(88,pitch));lastX=event.clientX;lastY=event.clientY;render()});
  stage.addEventListener('pointerup',()=>dragging=false);
  stage.addEventListener('wheel',event=>{event.preventDefault();zoom*=Math.exp(-event.deltaY*.001);
    zoom=Math.max(.2,Math.min(6,zoom));render()},{passive:false});
  window.addEventListener('resize',render);

  document.getElementById('title').textContent=manifest.label;
  document.getElementById('subtitle').textContent=`${manifest.kind} · ${manifest.dimensions_m.join(' × ')} m`;
  document.getElementById('pieces').textContent=manifest.pieces.toLocaleString();
  document.getElementById('triangles').textContent=(manifest.pieces*12).toLocaleString();
  document.getElementById('bytes').textContent=`${(manifest.instance_bytes/1048576).toFixed(2)} MiB`;
  document.getElementById('adapter').textContent=adapterInfo.description||adapterInfo.device||adapterInfo.vendor||adapterClass;
  if(manifest.live_endpoint) {
    const controls=document.getElementById('live-controls'),result=document.getElementById('live-result');
    const fields={x:document.getElementById('world-x'),y:document.getElementById('world-y'),
      z:document.getElementById('world-z'),yaw_degrees:document.getElementById('world-yaw')};
    const defaults=manifest.default_placement||{};
    for(const [key,input] of Object.entries(fields)) input.value=defaults[key]??'';
    controls.hidden=false;
    const buttons=[document.getElementById('apply-live'),document.getElementById('clear-live')];
    async function send(operation) {
      const body={};for(const [key,input] of Object.entries(fields))body[key]=Number(input.value);
      if(operation==='apply'&&!Object.values(body).every(Number.isFinite)) {
        result.textContent='BLOCKED\nEnter finite X, Y, Z, and yaw values.';return;
      }
      buttons.forEach(button=>button.disabled=true);
      result.textContent=`${operation} queued; waiting for the loaded mod receipt…`;
      try {
        const response=await fetch(`/api/${operation}`,{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify(body)}),payload=await response.json();
        result.textContent=JSON.stringify(payload,null,2);window.__liveReceipt=payload;
        if(!response.ok) throw new Error(payload.error||`HTTP ${response.status}`);
      } catch(error) { result.textContent=`BLOCKED\n${error.message}\n\n${result.textContent}`; }
      finally { buttons.forEach(button=>button.disabled=false); }
    }
    buttons[0].addEventListener('click',()=>send('apply'));
    buttons[1].addEventListener('click',()=>send('clear'));
  }
  setView(params.get('view')||'iso');setMode(mode);
  statusNode.textContent=`${adapterClass} · GPU scene submitted`;
  await device.queue.onSubmittedWorkDone();
  await frame();await frame();
  const startup=performance.now()-PAGE_STARTED;
  document.documentElement.dataset.ready='true';window.__webgpuReady=true;
  statusNode.textContent=`${adapterClass} · ${startup.toFixed(1)} ms start`;

  const base={schema:'webgpu-zdo-browser/v1',status:'ready',pieces:manifest.pieces,
    triangles:manifest.pieces*12,instance_bytes:manifest.instance_bytes,
    instance_stride:manifest.instance_stride,draw_calls:visible.size,adapter:adapterInfo,
    adapter_classification:adapterClass,features:[...adapter.features].sort(),
    canvas:[canvas.width,canvas.height],startup_ms:+startup.toFixed(2),
    validation_errors:errors,device_lost:deviceLost,user_agent:navigator.userAgent};
  publish(base);
  if(params.get('benchmark')==='1') {
    const intervals=[],submits=[];let previous=performance.now();
    for(let i=0;i<manifest.warmup_frames;i++) {yaw+=.7;render();await frame();previous=performance.now();}
    for(let i=0;i<manifest.benchmark_frames;i++) {
      const submitted=performance.now();yaw+=.7;render();submits.push(performance.now()-submitted);
      await frame();const now=performance.now();intervals.push(now-previous);previous=now;
    }
    await device.queue.onSubmittedWorkDone();
    publish({...base,status:'ok',samples:intervals.length,
      frame_p50_ms:+percentile(intervals,.5).toFixed(2),
      frame_p95_ms:+percentile(intervals,.95).toFixed(2),
      frame_max_ms:+Math.max(...intervals).toFixed(2),
      submit_p95_ms:+percentile(submits,.95).toFixed(3),
      validation_errors:errors,device_lost:deviceLost});
    statusNode.textContent=`${adapterClass} · ${percentile(intervals,.95).toFixed(2)} ms p95`;
  }
}
main().catch(fail);
</script>
</body>
</html>
'''


NODE_COLLECT = r'''
const pageUrl=process.argv[1],browserUrl=process.argv[2],timeoutMs=Number(process.argv[3]);
const pending=new Map();let nextId=1,done=false;
function connect(url){return new Promise((resolve,reject)=>{const ws=new WebSocket(url);
  ws.addEventListener('open',()=>resolve(ws));ws.addEventListener('error',()=>reject(new Error('websocket error')));});}
function attach(ws){ws.addEventListener('message',event=>{const m=JSON.parse(event.data);
  if(m.id&&pending.has(m.id)){const {resolve,reject}=pending.get(m.id);pending.delete(m.id);
    m.error?reject(new Error(m.error.message)):resolve(m.result);}});}
function call(ws,method,params={}){return new Promise((resolve,reject)=>{const id=nextId++;
  pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});}
function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
(async()=>{const page=await connect(pageUrl),browser=await connect(browserUrl);attach(page);attach(browser);
  const deadline=Date.now()+timeoutMs;let receipt=null;
  while(Date.now()<deadline){const r=await call(page,'Runtime.evaluate',{expression:
    'JSON.stringify(window.__webgpuReceipt || null)',returnByValue:true});
    const value=r.result&&r.result.value;if(typeof value==='string'&&value!=='null'){
      const parsed=JSON.parse(value);if(parsed.status!=='ready'){receipt=parsed;break;}}
    await sleep(100);}
  if(!receipt)throw new Error('WebGPU benchmark receipt timed out');
  const system=await call(browser,'SystemInfo.getInfo');
  process.stdout.write(JSON.stringify({page:receipt,system})+'\n');done=true;page.close();browser.close();
})().catch(error=>{process.stderr.write(error.stack+'\n');process.exitCode=2;});
setTimeout(()=>{if(!done){process.stderr.write('collector hard timeout\n');process.exit(2)}},timeoutMs+2000).unref();
'''


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cluster-points", type=Path, default=DEFAULT_CLUSTER_POINTS)
    ap.add_argument("--building-geometry", type=Path, default=DEFAULT_BUILDING_GEOMETRY)
    ap.add_argument("--piece-geometry", type=Path, default=ARCH / "piece-geometry.json")
    ap.add_argument("--rotation-verify", type=Path, default=ARCH / "rotation-verify.json")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--pilot-cluster", type=int, default=1820)
    ap.add_argument("--stress-cluster", type=int, default=182)
    ap.add_argument("--expected-pilot-pieces", type=int, default=847)
    ap.add_argument("--benchmark-frames", type=int, default=300)
    ap.add_argument("--warmup-frames", type=int, default=30)
    ap.add_argument("--startup-limit-ms", type=float, default=2000.0)
    ap.add_argument("--frame-p95-limit-ms", type=float, default=20.0)
    ap.add_argument("--browser", type=Path)
    ap.add_argument("--browser-timeout-s", type=float, default=60.0)
    ap.add_argument("--pilot-only", action="store_true")
    ap.add_argument("--no-browser", action="store_true")
    return ap.parse_args()


def hex_color(name):
    color = FAMILY_COLORS.get(name, FAMILY_COLORS["misc"])
    return "#%02x%02x%02x" % color[:3]


def encode_scene(pieces, label, kind, out_dir, benchmark_frames, warmup_frames):
    if not pieces:
        raise RuntimeError(f"cannot encode empty scene {label}")
    low, high = oriented_bounds(pieces)
    origin = (low + high) / 2.0
    dimensions = high - low
    mirror_x = np.diag([-1.0, 1.0, 1.0])
    ordered = sorted(pieces, key=lambda p: (p["family"], p["zdo"]))
    instances = np.empty((len(ordered), INSTANCE_FLOATS), dtype="<f4")
    families = []
    start = 0
    farthest = 0.0
    for family in sorted({p["family"] for p in ordered}):
        members = [p for p in ordered if p["family"] == family]
        families.append({"name": family, "color": hex_color(family),
                         "start": start, "count": len(members)})
        start += len(members)
    family_rgba = {
        family["name"]: [int(family["color"][i:i + 2], 16) / 255.0
                          for i in (1, 3, 5)] + [1.0]
        for family in families
    }
    for index, piece in enumerate(ordered):
        local_center = mirror_x @ (piece["center"] - origin)
        rotation = mirror_x @ piece["R"] @ mirror_x
        linear = rotation @ np.diag(piece["extents"])
        model = np.eye(4, dtype=np.float32)
        model[:3, :3] = linear
        model[:3, 3] = local_center
        instances[index, :16] = model.reshape(-1, order="F")
        instances[index, 16:] = family_rgba[piece["family"]]
        farthest = max(farthest, float(np.linalg.norm(local_center) +
                                      np.linalg.norm(piece["half"])))
    if not np.all(np.isfinite(instances)):
        raise RuntimeError(f"non-finite GPU instance in {label}")
    if instances.nbytes != len(ordered) * INSTANCE_BYTES:
        raise RuntimeError("instance stride receipt mismatch")

    out_dir.mkdir(parents=True, exist_ok=True)
    binary_path = out_dir / "scene.bin"
    manifest_path = out_dir / "scene.json"
    html_path = out_dir / "index.html"
    binary_path.write_bytes(instances.tobytes(order="C"))
    manifest = {
        "schema": "webgpu-zdo-scene/v1", "label": label, "kind": kind,
        "pieces": len(ordered), "triangles": len(ordered) * 12,
        "instance_stride": INSTANCE_BYTES, "instance_bytes": instances.nbytes,
        "dimensions_m": [round(float(value), 2) for value in dimensions],
        "radius_m": round(farthest, 3), "families": families,
        "benchmark_frames": benchmark_frames, "warmup_frames": warmup_frames,
        "coordinate_space": "cluster-local right-handed; absolute origin withheld",
    }
    manifest_path.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    html_path.write_text(HTML, encoding="utf-8")
    return manifest, {"html": str(html_path), "manifest": str(manifest_path),
                      "binary": str(binary_path), "binary_bytes": binary_path.stat().st_size}


def input_diagnostics(pieces):
    vegetation = Counter(piece["name"] for piece in pieces
                         if looks_like_vegetation(piece["name"]))
    largest = sorted(pieces, key=lambda piece: float(np.prod(piece["extents"])),
                     reverse=True)[:5]
    return {
        "vegetation_instances": sum(vegetation.values()),
        "vegetation_prefabs": dict(vegetation.most_common()),
        "largest_proxies": [
            {"prefab": piece["name"], "family": piece["family"],
             "extents_m": [round(float(value), 3) for value in piece["extents"]],
             "source": piece["source"]}
            for piece in largest
        ],
    }


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


@contextmanager
def localhost(directory):
    handler = functools.partial(QuietHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def webgpu_browser_base(browser, profile):
    return [str(browser), "--headless=new", "--no-first-run", "--disable-default-apps",
            "--disable-extensions", "--disable-background-networking",
            "--disable-component-update", "--disable-sync", "--metrics-recording-only",
            "--mute-audio", "--hide-scrollbars", "--run-all-compositor-stages-before-draw",
            "--disable-renderer-backgrounding", "--disable-background-timer-throttling",
            "--enable-features=WebGPUDeveloperFeatures", f"--user-data-dir={profile}"]


def wait_for_devtools(profile, process, timeout_s):
    active = Path(profile) / "DevToolsActivePort"
    deadline = time.monotonic() + min(12.0, timeout_s / 2)
    while not active.is_file() and time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"browser exited {process.returncode}")
        time.sleep(0.05)
    if not active.is_file():
        raise TimeoutError("DevToolsActivePort was not created")
    lines = active.read_text(encoding="utf-8").splitlines()
    return lines[0], f"ws://127.0.0.1:{lines[0]}{lines[1]}"


def page_target(port, url, timeout_s):
    deadline = time.monotonic() + min(12.0, timeout_s / 2)
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/json/list", timeout=1) as response:
                targets = json.load(response)
            target = next((item for item in targets if item.get("type") == "page" and
                           url.split("?")[0] in item.get("url", "")), None)
            if target:
                return target
        except OSError:
            pass
        time.sleep(0.05)
    raise TimeoutError("benchmark page target was not created")


def close_browser(process):
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def trim_system_info(system):
    gpu = system.get("gpu", {}) if isinstance(system, dict) else {}
    return {
        "devices": gpu.get("devices", []),
        "aux_attributes": gpu.get("auxAttributes", {}),
        "feature_status": gpu.get("featureStatus", {}),
        "model_name": system.get("modelName", "") if isinstance(system, dict) else "",
        "model_version": system.get("modelVersion", "") if isinstance(system, dict) else "",
    }


def run_benchmark(browser, url, timeout_s):
    node = shutil.which("node")
    if not node:
        return {"status": "node_not_found"}
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(
            prefix="webgpu-zdo-browser-", ignore_cleanup_errors=True) as profile:
        command = webgpu_browser_base(browser, profile) + [
            "--remote-debugging-port=0", "--remote-allow-origins=*",
            "--window-size=1600,1000", url]
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        try:
            port, browser_ws = wait_for_devtools(profile, process, timeout_s)
            target = page_target(port, url, timeout_s)
            remaining = max(1.0, timeout_s - (time.perf_counter() - started))
            collect = subprocess.run(
                [node, "-e", NODE_COLLECT, target["webSocketDebuggerUrl"], browser_ws,
                 str(int(remaining * 1000))], capture_output=True, text=True,
                timeout=remaining + 3, encoding="utf-8", errors="replace")
            if collect.returncode:
                return {"status": "receipt_missing", "stderr_tail": collect.stderr[-1600:]}
            wrapper = json.loads(collect.stdout.strip())
            receipt = wrapper["page"]
            receipt["system_gpu"] = trim_system_info(wrapper.get("system", {}))
            receipt["wall_ms"] = round((time.perf_counter() - started) * 1000, 2)
            return receipt
        except (RuntimeError, TimeoutError, subprocess.TimeoutExpired,
                json.JSONDecodeError) as exc:
            return {"status": "browser_error", "error": str(exc),
                    "wall_ms": round((time.perf_counter() - started) * 1000, 2)}
        finally:
            close_browser(process)


def capture(browser, url, path, timeout_s):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
            prefix="webgpu-zdo-capture-", ignore_cleanup_errors=True) as profile:
        command = webgpu_browser_base(browser, profile) + [
            "--window-size=1600,1000", "--force-device-scale-factor=1",
            "--virtual-time-budget=8000", f"--screenshot={path.resolve()}", url]
        try:
            process = subprocess.run(command, capture_output=True, text=True,
                                     timeout=timeout_s, encoding="utf-8", errors="replace")
        except subprocess.TimeoutExpired:
            return {"status": "browser_timeout", "path": str(path)}
    if process.returncode or not path.is_file():
        return {"status": "capture_error", "returncode": process.returncode,
                "path": str(path), "stderr_tail": process.stderr[-1200:]}
    return {"status": "ok", "path": str(path), "bytes": path.stat().st_size}


def hardware_class(receipt):
    page_class = receipt.get("adapter_classification", "unknown")
    adapter_text = json.dumps(receipt.get("adapter", {})).lower()
    if any(token in adapter_text for token in
           ("swiftshader", "llvmpipe", "software rasterizer", "warp", "cpu")):
        return "software"
    if page_class == "hardware":
        return "hardware"
    active = receipt.get("system_gpu", {}).get("aux_attributes", {})
    active_text = json.dumps({
        "renderer": active.get("glRenderer", ""),
        "vendor": active.get("glVendor", ""),
    }).lower()
    if any(token in active_text for token in
           ("swiftshader", "llvmpipe", "software rasterizer", "microsoft basic render", "warp")):
        return "software"
    if any(token in active_text for token in
           ("intel", "nvidia", "amd", "radeon", "arc", "geforce")):
        return "hardware"
    return "unknown"


def gate(receipt, expected_pieces, startup_limit, frame_limit):
    classification = hardware_class(receipt)
    receipt["hardware_gate"] = classification
    reasons = []
    if receipt.get("status") != "ok":
        reasons.append(f"status={receipt.get('status')}")
    if receipt.get("pieces") != expected_pieces:
        reasons.append(f"pieces={receipt.get('pieces')} expected={expected_pieces}")
    if classification != "hardware":
        reasons.append(f"adapter={classification}")
    if receipt.get("startup_ms", math.inf) > startup_limit:
        reasons.append(f"startup={receipt.get('startup_ms')}ms")
    if receipt.get("frame_p95_ms", math.inf) > frame_limit:
        reasons.append(f"p95={receipt.get('frame_p95_ms')}ms")
    if receipt.get("validation_errors"):
        reasons.append(f"validation_errors={len(receipt['validation_errors'])}")
    if receipt.get("device_lost"):
        reasons.append("device_lost")
    return not reasons, reasons


def scene_url(origin, out_root, scene_dir, query):
    relative = scene_dir.resolve().relative_to(out_root.resolve()).as_posix()
    return f"{origin}/{quote(relative)}/index.html?{query}"


def main():
    args = parse_args()
    winner, (to_rad, compose) = load_rotation_receipt(args.rotation_verify)
    geometry = load_geometry(args.piece_geometry)
    con = duckdb.connect()
    pilot_all, pilot_join = load_cluster(
        con, args.pilot_cluster, args.cluster_points, args.building_geometry,
        geometry, to_rad, compose)
    components = segment(pilot_all)
    pilot = [pilot_all[index] for index in components[0]]
    if len(pilot) != args.expected_pilot_pieces:
        raise RuntimeError(
            f"pilot main component {len(pilot)} != {args.expected_pilot_pieces}")
    stress, stress_join = load_cluster(
        con, args.stress_cluster, args.cluster_points, args.building_geometry,
        geometry, to_rad, compose)

    pilot_dir = args.out / "pilot-1820"
    stress_dir = args.out / "stress-182"
    pilot_manifest, pilot_artifact = encode_scene(
        pilot, f"Cluster {args.pilot_cluster}", "complete connected structure",
        pilot_dir, args.benchmark_frames, args.warmup_frames)
    stress_manifest, stress_artifact = encode_scene(
        stress, f"Cluster {args.stress_cluster}", "complete frozen known-geometry cluster",
        stress_dir, args.benchmark_frames, args.warmup_frames)

    browser = None if args.no_browser else find_browser(args.browser)
    report = {
        "schema": "webgpu-zdo-rnd/v1", "rotation_verdict": "PASS",
        "rotation_decode": winner, "renderer": "WebGPU instanced unit cubes",
        "fallbacks": [], "instance_stride": INSTANCE_BYTES,
        "pilot": {"join": pilot_join, "components": len(components),
                  "main_component_pieces": len(pilot), "scene": pilot_manifest,
                  "artifact": pilot_artifact, "input_diagnostics": input_diagnostics(pilot)},
        "stress": {"join": stress_join, "scene": stress_manifest,
                   "artifact": stress_artifact, "input_diagnostics": input_diagnostics(stress)},
        "gate": {"startup_limit_ms": args.startup_limit_ms,
                 "frame_p95_limit_ms": args.frame_p95_limit_ms,
                 "warmup_frames": args.warmup_frames,
                 "benchmark_frames": args.benchmark_frames,
                 "viewport": [1600, 1000]},
        "browser": str(browser) if browser else None, "captures": [],
        "uncertainties": [
            "oriented prefab boxes are massing proxies, not render meshes",
            "headless Edge may choose a different adapter or presentation path than a visible window",
            "requestAdapter high-performance is a preference rather than a specific-GPU guarantee",
            "frame intervals include browser presentation and JavaScript submission, not GPU timestamps",
            "opaque solids and lines do not test transparency, terrain, textures, picking, or culling",
            "188 frozen cluster-182 members have no known prefab geometry and are omitted",
        ],
    }

    args.out.mkdir(parents=True, exist_ok=True)
    if not browser:
        report["edge"] = {"status": "BLOCKED", "reason": "browser unavailable"}
    else:
        with localhost(args.out) as origin:
            pilot_benchmark_url = scene_url(
                origin, args.out, pilot_dir, "benchmark=1&view=iso&mode=solid")
            pilot_benchmark = run_benchmark(
                browser, pilot_benchmark_url, args.browser_timeout_s)
            pilot_pass, pilot_reasons = gate(
                pilot_benchmark, len(pilot), args.startup_limit_ms,
                args.frame_p95_limit_ms)
            report["pilot"]["benchmark"] = pilot_benchmark
            report["pilot"]["mechanical_gate"] = "PASS" if pilot_pass else "FAIL"
            report["pilot"]["gate_reasons"] = pilot_reasons

            for filename, view, mode in (
                    ("isometric-solid.png", "iso", "solid"),
                    ("end-078.8-solid.png", "end-a", "solid"),
                    ("end-258.8-wire.png", "end-b", "wire")):
                url = scene_url(origin, args.out, pilot_dir,
                                f"view={view}&mode={mode}&capture=1")
                item = capture(browser, url, pilot_dir / filename, args.browser_timeout_s)
                item.update({"scene": "pilot", "view": view, "mode": mode})
                report["captures"].append(item)

            if not pilot_pass:
                report["edge"] = {"status": "FOUND", "at": "pilot",
                                  "pieces": len(pilot), "reasons": pilot_reasons}
            elif args.pilot_only:
                report["edge"] = {"status": "PILOT_PASS", "stress": "not requested"}
            else:
                stress_url = scene_url(
                    origin, args.out, stress_dir, "benchmark=1&view=iso&mode=solid")
                stress_benchmark = run_benchmark(browser, stress_url, args.browser_timeout_s)
                stress_pass, stress_reasons = gate(
                    stress_benchmark, len(stress), args.startup_limit_ms,
                    args.frame_p95_limit_ms)
                report["stress"]["benchmark"] = stress_benchmark
                report["stress"]["mechanical_gate"] = "PASS" if stress_pass else "FAIL"
                report["stress"]["gate_reasons"] = stress_reasons
                for filename, mode in (("isometric-solid.png", "solid"),
                                       ("isometric-wire.png", "wire")):
                    url = scene_url(origin, args.out, stress_dir,
                                    f"view=iso&mode={mode}&capture=1")
                    item = capture(browser, url, stress_dir / filename,
                                   args.browser_timeout_s)
                    item.update({"scene": "stress", "view": "iso", "mode": mode})
                    report["captures"].append(item)
                report["edge"] = ({"status": "NOT_REACHED", "sampled_pieces": len(stress),
                                   "triangles": len(stress) * 12}
                                  if stress_pass else
                                  {"status": "FOUND", "at": "full_stress",
                                   "pieces": len(stress), "reasons": stress_reasons})

    result_path = args.out / "result.json"
    result_path.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"pilot: {len(pilot)} instances / {len(pilot)*12} triangles", flush=True)
    print(f"stress: {stress_join['frozen_members']} frozen / {len(stress)} known geometry / "
          f"{len(stress)*INSTANCE_BYTES} bytes",
          flush=True)
    print(f"edge: {report['edge']}", flush=True)
    print(f"wrote {result_path}", flush=True)


if __name__ == "__main__":
    main()
