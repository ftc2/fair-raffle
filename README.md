# fair-raffle

## Description

A simple algorithm and python script to conduct provably fair raffles. Tickets are generated in a dependent chain, and winner(s) are selected using output from a [public source of entropy](https://www.nist.gov/programs-projects/nist-randomness-beacon) at a pre-determined time in the future.

## Algorithm

Consider a list of *N* entrants (i.e. potential raffle winners) and define `+` as the string concatenation operator.

For each entrant *E<sub>i</sub>*, a hash *H<sub>i</sub>* is first computed:

&nbsp;&nbsp;&nbsp;&nbsp;<a href="https://www.codecogs.com/eqnedit.php?latex=H_{i}=\big(\texttt{SHA256}(E_{i}&plus;i)\big)_{i=1}^{N}" target="_blank"><img src="https://latex.codecogs.com/gif.latex?H_{i}=\big(\texttt{SHA256}(E_{i}&plus;i)\big)_{i=1}^{N}" title="H_{i}=\big(\texttt{SHA256}(E_{i}+i)\big)_{i=1}^{N}" /></a>

Next, each raffle ticket *T<sub>i</sub>* in the chain is computed letting the raffle name *name* serve as a seed:

&nbsp;&nbsp;&nbsp;&nbsp;<a href="https://www.codecogs.com/eqnedit.php?latex=T_{i}=\qquad&space;\begin{cases}&space;\texttt{SHA256}(\mathrm{name}&plus;H_{i}),&space;&&space;i=&space;1\\&space;\texttt{SHA256}(T_{i-1}&plus;H_{i}),&space;&&space;2\leq&space;i\leq&space;N&space;\end{cases}" target="_blank"><img src="https://latex.codecogs.com/gif.latex?T_{i}=\qquad&space;\begin{cases}&space;\texttt{SHA256}(\mathrm{name}&plus;H_{i}),&space;&&space;i=&space;1\\&space;\texttt{SHA256}(T_{i-1}&plus;H_{i}),&space;&&space;2\leq&space;i\leq&space;N&space;\end{cases}" title="T_{i}=\qquad \begin{cases} \texttt{SHA256}(\mathrm{name}+H_{i}), & i= 1\\ \texttt{SHA256}(T_{i-1}+H_{i}), & 2\leq i\leq N \end{cases}" /></a>

Note that each ticket depends on the previous tickets in the chain making it impossible to cheat by retroactively injecting tickets. 

Finally, the raffle drawing is conducted by calculating a result *R<sub>i</sub>* for each ticket:

&nbsp;&nbsp;&nbsp;&nbsp;<a href="https://www.codecogs.com/eqnedit.php?latex=R_{i}=\big(\texttt{SHA256}(T_{i}&plus;P)\big)_{i=1}^{N}" target="_blank"><img src="https://latex.codecogs.com/gif.latex?R_{i}=\big(\texttt{SHA256}(T_{i}&plus;P)\big)_{i=1}^{N}" title="R_{i}=\big(\texttt{SHA256}(T_{i}+P)\big)_{i=1}^{N}" /></a>

where *P* the NIST Randomness Beacon's [output](https://beacon.nist.gov/home) (512 bits of entropy) at the pre-determined moment of the drawing.

The winning ticket is the one with the lowest result. If multiple winners are desired, the *n<sup>th</sup>* winner holds the ticket with the *n<sup>th</sup>* lowest result.

## Python script: fair-raffle.py

### Requirements

Works with python 2.7.15

### Usage


```
usage: fair-raffle.py [-h] [-i PULSE | -u PULSE | -t PULSE | -l] ENTRANTS

Provably Fair Raffle Generator

positional arguments:
  ENTRANTS    path to text file containing raffle entrants (one name per line,
              lines beginning with "#" are ignored)

optional arguments:
  -h, --help  show this help message and exit
  -i PULSE    index of NIST Randomness Beacon pulse used to select winners
  -u PULSE    Unix timestamp (in ms) of NIST Randomness Beacon pulse used to
              select winners
  -t PULSE    timestamp of NIST Randomness Beacon pulse used to select
              winners. format: "year-month-day hour-minute timezone", e.g.
              "2018-11-28 16:03 -0600" or "2018-11-28 22:03 +0000"
  -l          use latest available NIST Randomness Beacon pulse to select
              winners

Generates a raffle ticket chain for the entrants provided. If an NIST
Randomness Beacon (https://beacon.nist.gov/home) pulse is specified, the
raffle drawing is conducted. Raffle tickets and (optionally) sorted results
are written to CSV files.
```

#### Example

For a raffle named `my_raffle`:

First, publicly announce the date and time (down to the minute) on which the raffle drawing will occur. Let the cutoff in this example be `2018-11-28 22:03 -0600` (i.e. 10:03 PM [CST](https://en.wikipedia.org/wiki/UTC%E2%88%9206:00) on 2018-11-28).

Collect the names of the raffle entrants and put them in a text file `my_raffle.txt` (one entrant per line). Entering someone multiple times proportionally increases their chances of winning.

Generate tickets like this:

    python fair-raffle.py /path/to/my_raffle.txt

The ticket chain will be saved to `my_raffle-ticketchain.csv`. I suggest making an up-to-date version of this file available to the entrants so that they have their tickets and can inspect the chain. Crucially, entrants must have access to their tickets before the time of the drawing.

As you collect more entrants, update `my_raffle.txt` and re-generate the tickets. Note that you should only *append* to `my_raffle.txt`. Any rearrangement or injection corrupts the ticket chain by design.

At any time *after* the announced drawing time, find winner(s) like this:

```
python fair-raffle.py /path/to/my_raffle.txt -t '2018-11-28 22:03 -0600'

Parsed 10 raffle entrants.
Fetching https://beacon.nist.gov/beacon/2.0/pulse/time/1543464180000 ...
NIST Randomness Beacon output for pulse index 180921 (2018-11-29T04:03:00.000Z): https://beacon.nist.gov/beacon/2.0/chain/1/pulse/180921
  00C1D306216BD4B4DC183292E92DEC7842B0C0AF0FB2EF8EE7A057E2240A620EC4971D579A69DABCB134850C1C62B4D0C25EEEED68E83B2BC4FB091BEBE7D176
Winner: bill (for details, see /path/to/my_raffle-results-180921.csv)
```

The results of the drawing will be saved to `my_raffle-results-<pulseIndex>.csv`. They're sorted so that winners come first. If you want only one winner, just pick the first in the list.

See also provided sample entrants, tickets, and sorted results.
