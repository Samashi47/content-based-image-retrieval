import { Injectable } from '@angular/core';
import { tick } from '@angular/core/testing';
import * as Plotly from 'plotly.js-dist-min';

@Injectable({
  providedIn: 'root',
})
export class PlotlyService {
  constructor() {}

  plotHist(plotDiv: string, R: number[], G: number[], B: number[]) {
    const x = Array.from({ length: 256 }, (_, i) => i);
    const traceR: Plotly.Data = {
      x: x,
      y: R,
      mode: 'lines',
      opacity: 0.5,
      name: 'R',
      marker: {
        color: 'red',
      },
    };
    const traceG: Plotly.Data = {
      x: x,
      y: G,
      mode: 'lines',
      opacity: 0.5,
      name: 'G',
      marker: {
        color: 'green',
      },
    };
    const traceB: Plotly.Data = {
      x: x,
      y: B,
      mode: 'lines',
      opacity: 0.5,
      name: 'B',
      marker: {
        color: 'blue',
      },
    };
    const data = [traceR, traceG, traceB];
    const layout: Partial<Plotly.Layout> = {
      title: {
        text: 'Color Histogram',
      },
      font: {
        family: 'Roboto',
      },
      plot_bgcolor: 'rgba(250, 249, 253, 1)',
      paper_bgcolor: 'rgba(250, 249, 253, 1)',
      width: 512,
      xaxis: {
        title: {
          text: 'Color Intensity',
          font: {
            family: 'Roboto',
          },
        },
        tickfont: {
          family: 'Roboto',
        },
      },
      yaxis: {
        title: {
          text: 'Frequency',
          font: {
            family: 'Roboto',
          },
        },
        tickfont: {
          family: 'Roboto',
        },
      },
      margin: {
        l: 68,
        r: 0,
        t: 84,
        b: 68,
      },
    };

    Plotly.newPlot(plotDiv, data, layout);
  }

  plotDominantColors(plotDiv: string, colors: number[][]) {
    // convert colors matrix to array of strings
    const dominantColors = colors.map(
      (color) => `rgb(${color[0]}, ${color[1]}, ${color[2]})`
    );
    console.log('Dominant Colors:', dominantColors);
    const data: Plotly.Data = {
      values: Array.from({ length: colors.length }, (_, i) => 1),
      labels: colors.map((color, i) => `Color ${i + 1}`),
      type: 'pie',
      marker: {
        colors: dominantColors,
      },
      hoverinfo: 'none',
      textinfo: 'none',
    };
    const layout: Partial<Plotly.Layout> = {
      title: {
        text: 'Dominant Colors',
      },
      font: {
        family: 'Roboto',
      },
      plot_bgcolor: 'rgba(250, 249, 253, 1)',
      paper_bgcolor: 'rgba(250, 249, 253, 1)',
      width: 512,
      showlegend: false,
    };

    Plotly.newPlot(plotDiv, [data], layout);
  }
}
