# Salt okunur Windows bellek gozlemi; Ollama/ag/servis islemi yoktur.
function Initialize-WP12LowMemoryNative {
    if ('WP12LowMemoryNativeV1' -as [type]) { return }
    Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
public static class WP12LowMemoryNativeV1 {
 [StructLayout(LayoutKind.Sequential)] public struct Memory {
  public uint length,load; public ulong total,available,totalPage,freePage,totalVirtual,freeVirtual,extended;
 }
 [StructLayout(LayoutKind.Sequential)] public struct Performance {
  public uint cb; public UIntPtr CommitTotal,CommitLimit,CommitPeak,PhysicalTotal,PhysicalAvailable,SystemCache,KernelTotal,KernelPaged,KernelNonpaged,PageSize;
  public uint HandleCount,ProcessCount,ThreadCount;
 }
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GlobalMemoryStatusEx(ref Memory m);
 [DllImport("psapi.dll",SetLastError=true)] static extern bool GetPerformanceInfo(ref Performance p,uint cb);
 [DllImport("kernel32.dll",SetLastError=true)] static extern IntPtr CreateMemoryResourceNotification(int kind);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool QueryMemoryResourceNotification(IntPtr h,out bool state);
 [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool OpenProcessToken(IntPtr p,uint a,out IntPtr t);
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool GetTokenInformation(IntPtr t,int k,out int v,int n,out int r);
 [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
 public static Memory ReadMemory() { Memory m=new Memory();m.length=(uint)Marshal.SizeOf(typeof(Memory));
  if(!GlobalMemoryStatusEx(ref m)) throw new Win32Exception();return m; }
 public static ulong ReadCommitAvailable() {Performance p=new Performance();p.cb=(uint)Marshal.SizeOf(typeof(Performance));
  if(!GetPerformanceInfo(ref p,p.cb)) throw new Win32Exception();return (p.CommitLimit.ToUInt64()-p.CommitTotal.ToUInt64())*p.PageSize.ToUInt64();}
 public static bool ReadLowMemoryPressure() {IntPtr h=CreateMemoryResourceNotification(0);
  if(h==IntPtr.Zero) throw new Win32Exception();try {bool state;if(!QueryMemoryResourceNotification(h,out state)) throw new Win32Exception();return state;}
  finally {CloseHandle(h);} }
 public static bool IsAppContainer() {IntPtr t;if(!OpenProcessToken(GetCurrentProcess(),8,out t)) throw new Win32Exception();
  try {int v,r;if(!GetTokenInformation(t,29,out v,4,out r)) throw new Win32Exception();return v!=0;}finally {CloseHandle(t);}}
}
'@
}
function Get-WP12LowMemorySample {
    $m=[WP12LowMemoryNativeV1]::ReadMemory()
    return @{at=[DateTimeOffset]::Now.ToString('o');available_bytes=$m.available;total_bytes=$m.total;
        load_percent=$m.load;commit_available_bytes=[WP12LowMemoryNativeV1]::ReadCommitAvailable();
        low_memory_notification=[WP12LowMemoryNativeV1]::ReadLowMemoryPressure()}
}
