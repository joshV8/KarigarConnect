Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SetOutputToWaveFile("$PSScriptRoot\real_speech.wav")
$synth.Speak("This is a handmade wooden and bamboo basket crafted by local artisans")
$synth.Dispose()
Write-Host "Generated speech successfully"
